from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class OperationalIntelligenceService:
    """Deterministic operational timeline/status layer over existing simulation data.

    Business simulation remains the source of truth. This service only derives
    timeline/status/recommendation metadata from facts already present in the
    pipeline response.
    """

    VERSION = "1.0"

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _list(value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _num(value: Any, default: float = 0.0) -> float:
        try:
            result = float(value)
            return result if result == result else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _round(value: Any, digits: int = 2) -> float:
        return round(OperationalIntelligenceService._num(value), digits)

    @classmethod
    def _business(cls, raw: dict[str, Any]) -> dict[str, Any]:
        return cls._dict(raw.get("business_supply_chain"))

    @classmethod
    def _simulations(cls, raw: dict[str, Any]) -> list[dict[str, Any]]:
        business = cls._business(raw)
        container = cls._dict(business.get("simulation"))
        simulations = container.get("simulations")
        if not isinstance(simulations, list):
            simulations = business.get("simulations")
        return [cls._dict(item) for item in cls._list(simulations)]

    @classmethod
    def _component_rows(cls, raw: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for item in cls._simulations(raw):
            simulation = cls._dict(item.get("simulation"))
            supplier = cls._dict(item.get("supplier"))
            supplier_id = str(supplier.get("supplier_id") or "unknown")

            for component in cls._list(simulation.get("components")):
                component = cls._dict(component)
                component_id = str(component.get("component_id") or "unknown")
                plant_id = str(component.get("plant_id") or "unknown")
                key = (supplier_id, component_id, plant_id)
                if key in seen:
                    continue
                seen.add(key)
                rows.append({**component, "supplier_id": supplier_id})

        return rows

    @classmethod
    def _product_rows(cls, raw: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()

        for item in cls._simulations(raw):
            simulation = cls._dict(item.get("simulation"))
            for product in cls._list(simulation.get("products")):
                product = cls._dict(product)
                key = (
                    str(product.get("product_id") or "unknown"),
                    str(product.get("component_id") or "unknown"),
                    str(product.get("plant_id") or "unknown"),
                )
                if key in seen:
                    continue
                seen.add(key)
                rows.append(product)

        return rows

    @classmethod
    def _status_for_component(cls, component: dict[str, Any]) -> str:
        if bool(component.get("production_stop")):
            return "STOPPED"

        net_shortage = cls._num(component.get("net_shortage"))
        daily_demand = cls._num(component.get("daily_demand"))
        inventory = cls._num(component.get("inventory_quantity"))
        recovery = cls._num(component.get("alternative_recovery"))
        gross_shortage = cls._num(component.get("gross_shortage"))
        delay = cls._num(component.get("estimated_delay_days"))

        if net_shortage > 0:
            if daily_demand > 0 and net_shortage >= daily_demand:
                return "STOPPED"
            return "REDUCED"

        if delay > 0:
            return "BUFFERED" if inventory > 0 else "AT_RISK"

        if gross_shortage > 0 and recovery > 0:
            return "BUFFERED"

        if gross_shortage > 0 and inventory > 0:
            return "BUFFERED"

        if gross_shortage > 0:
            return "AT_RISK"

        return "RUNNING"

    @classmethod
    def _timeline_for_component(cls, component: dict[str, Any]) -> dict[str, Any]:
        inventory = cls._num(component.get("inventory_quantity"))
        daily_demand = cls._num(component.get("daily_demand"))
        gross_shortage = cls._num(component.get("gross_shortage"))
        net_shortage = cls._num(component.get("net_shortage"))
        recovery = cls._num(component.get("alternative_recovery"))
        route_delay = cls._num(component.get("route_disruption_delay_days"))
        estimated_delay = cls._num(component.get("estimated_delay_days"))

        buffer_days = inventory / daily_demand if daily_demand > 0 else None

        recovery_days: list[float] = []
        for alternative in cls._list(component.get("alternative_suppliers")):
            alternative = cls._dict(alternative)
            recoverable = cls._num(alternative.get("recoverable_supply_units"))
            lead_time = cls._num(alternative.get("lead_time_days"))
            if recoverable > 0 and lead_time >= 0:
                recovery_days.append(lead_time)

        first_recovery_day = min(recovery_days) if recovery_days else None
        first_shortage_day = None

        if net_shortage > 0:
            first_shortage_day = 0.0
        elif gross_shortage > 0 and daily_demand > 0 and inventory > 0:
            first_shortage_day = buffer_days
        elif gross_shortage > 0 and inventory <= 0:
            first_shortage_day = 0.0

        recovery_protects_buffer = (
            first_recovery_day is not None
            and buffer_days is not None
            and first_recovery_day <= buffer_days
        )

        if recovery_protects_buffer:
            status = "BUFFERED"
        else:
            status = cls._status_for_component(component)

        impact_window = None
        if first_recovery_day is not None and first_shortage_day is not None:
            impact_window = max(0.0, first_recovery_day - first_shortage_day)

        return {
            "component_id": component.get("component_id"),
            "component_name": component.get("component_name"),
            "plant_id": component.get("plant_id"),
            "plant_name": component.get("plant_name"),
            "supplier_id": component.get("supplier_id"),
            "status": status,
            "inventory_units": round(inventory, 2),
            "daily_demand_units": round(daily_demand, 2),
            "gross_shortage_units": round(gross_shortage, 2),
            "net_shortage_units": round(net_shortage, 2),
            "recovery_units": round(recovery, 2),
            "buffer_days": cls._round(buffer_days) if buffer_days is not None else None,
            "first_shortage_day": cls._round(first_shortage_day) if first_shortage_day is not None else None,
            "first_recovery_day": cls._round(first_recovery_day) if first_recovery_day is not None else None,
            "route_disruption_delay_days": round(route_delay, 2),
            "estimated_delay_days": round(estimated_delay, 2),
            "impact_window_days": cls._round(impact_window) if impact_window is not None else None,
            "recovery_protects_buffer": recovery_protects_buffer,
        }

    @classmethod
    def _overall_status(cls, component_timeline: list[dict[str, Any]], summary: dict[str, Any]) -> str:
        if bool(summary.get("production_stop")) or any(x["status"] == "STOPPED" for x in component_timeline):
            return "STOPPED"
        if any(x["status"] == "REDUCED" for x in component_timeline):
            return "REDUCED"
        if any(x["status"] == "AT_RISK" for x in component_timeline):
            return "AT_RISK"
        if component_timeline and all(x["status"] == "BUFFERED" for x in component_timeline):
            return "BUFFERED"
        return "RUNNING"

    @classmethod
    def _recommendations(cls, raw: dict[str, Any], timeline: dict[str, Any]) -> list[dict[str, Any]]:
        business = cls._business(raw)
        summary = cls._dict(business.get("summary"))
        if not summary:
            simulation = cls._dict(business.get("simulation"))
            summary = cls._dict(simulation.get("summary"))

        recommendations: list[dict[str, Any]] = []
        component_rows = timeline.get("components", [])

        net_shortage = cls._num(summary.get("net_shortage"))
        recovery = cls._num(summary.get("alternative_recovery"))
        gross_shortage = cls._num(summary.get("gross_shortage"))
        route_delay = cls._num(summary.get("max_route_disruption_delay_days"))

        if net_shortage > 0:
            recommendations.append({
                "priority": "critical",
                "action": "Activate alternate supply or procurement recovery for the remaining shortage.",
                "reason": f"Net shortage is {round(net_shortage, 2):g} units.",
            })
        elif gross_shortage > 0:
            recommendations.append({
                "priority": "high",
                "action": "Monitor inventory burn-down against recovery lead time.",
                "reason": f"Gross shortage is {round(gross_shortage, 2):g} units while inventory buffers the modeled shortage.",
            })

        at_risk = [x for x in component_rows if x.get("status") in {"AT_RISK", "REDUCED", "STOPPED"}]
        if at_risk:
            names = ", ".join(str(x.get("component_name") or x.get("component_id")) for x in at_risk[:3])
            recommendations.append({
                "priority": "high",
                "action": "Prioritize the components approaching operational exposure.",
                "reason": f"Affected components: {names}.",
            })

        if route_delay > 0:
            recommendations.append({
                "priority": "medium",
                "action": "Review alternate transportation paths for disrupted routes.",
                "reason": f"Maximum modeled route disruption delay is {round(route_delay, 2):g} days.",
            })

        if gross_shortage > 0 and recovery <= 0:
            recommendations.append({
                "priority": "high",
                "action": "Evaluate additional supplier capacity.",
                "reason": "No alternative recovery units are currently modeled.",
            })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "action": "Continue monitoring affected supply-chain dependencies.",
                "reason": "No immediate operational shortage action is required by the current model.",
            })

        return recommendations

    @classmethod
    def build(cls, raw: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raw = {}

        business = cls._business(raw)
        summary = cls._dict(business.get("summary"))
        if not summary:
            summary = cls._dict(cls._dict(business.get("simulation")).get("summary"))

        components = [cls._timeline_for_component(x) for x in cls._component_rows(raw)]
        products = cls._product_rows(raw)

        overall_status = cls._overall_status(components, summary)

        buffer_values = [x["buffer_days"] for x in components if x.get("buffer_days") is not None]
        shortage_days = [x["first_shortage_day"] for x in components if x.get("first_shortage_day") is not None]
        recovery_days = [x["first_recovery_day"] for x in components if x.get("first_recovery_day") is not None]

        timeline = {
            "version": cls.VERSION,
            "production_status": overall_status,
            "components": components,
            "products": products,
            "summary": {
                "affected_components": len({x.get("component_id") for x in components if x.get("component_id")}),
                "affected_products": len({x.get("product_id") for x in products if x.get("product_id")}),
                "affected_plants": len({x.get("plant_id") for x in components if x.get("plant_id")}),
                "minimum_buffer_days": round(min(buffer_values), 2) if buffer_values else None,
                "maximum_buffer_days": round(max(buffer_values), 2) if buffer_values else None,
                "first_shortage_day": round(min(shortage_days), 2) if shortage_days else None,
                "first_recovery_day": round(min(recovery_days), 2) if recovery_days else None,
                "gross_lost_supply": cls._round(summary.get("gross_lost_supply")),
                "alternative_recovery": cls._round(summary.get("alternative_recovery")),
                "gross_shortage": cls._round(summary.get("gross_shortage")),
                "net_shortage": cls._round(summary.get("net_shortage")),
                "max_delay_days": cls._round(summary.get("max_delay_days")),
                "max_route_disruption_delay_days": cls._round(summary.get("max_route_disruption_delay_days")),
            },
        }

        timeline["recommendations"] = cls._recommendations(raw, timeline)

        event = cls._dict(raw.get("event"))
        audit = {
            "event_id": event.get("event_id", event.get("id")),
            "source": event.get("source"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "operational_intelligence_version": cls.VERSION,
            "business_source_of_truth": "business_supply_chain.simulation",
            "ml_override": False,
        }

        return {
            "operational_timeline": timeline,
            "operational_audit": audit,
        }
