from app.core.database import SessionLocal
from app.models import Event, Supplier, Product, SupplyChainLink


def seed_database() -> None:
    """
    Seed initial Mohilya Couture Pvt Ltd (Surat Garment Supply Chain)
    data for legacy MVP compatibility tables (Supplier, Product, Event, SupplyChainLink).
    """
    db = SessionLocal()

    try:
        if db.query(Event).count() > 0:
            print("Database already contains event/supply-chain data.")
            return

        # ---------------------------------------------------------
        # EVENTS (Surat Textile & Apparel Disruption Scenarios)
        # ---------------------------------------------------------

        events = [
            Event(
                title="Surat Ring Road Textile Market Monsoon Inundation",
                description="Heavy torrential rainfall and waterlogging across Ring Road textile markets disrupt fabric loading and merchant outbound dispatch.",
                source="Surat Daily Dispatch",
                event_type="weather_disruption",
                location="Ring Road, Surat, India",
                severity=4,
                status="active",
            ),
            Event(
                title="Pandesara GIDC Industrial Power Grid Transformer Failure",
                description="High-voltage substation failure at Pandesara GIDC causes rolling power cuts across dyeing and digital printing processing units.",
                source="Gujarat Industrial News",
                event_type="infrastructure_failure",
                location="Pandesara GIDC, Surat, India",
                severity=4,
                status="active",
            ),
            Event(
                title="Bhagal & Salabatpura Zari Artisan Labor Wage Dispute",
                description="Artisans and trim merchants in Bhagal & Salabatpura initiate a temporary work stoppage delaying fancy lace, moti, and latkan supplies.",
                source="Surat Textile Bulletin",
                event_type="labor_strike",
                location="Bhagal-Salabatpura, Surat, India",
                severity=3,
                status="active",
            ),
            Event(
                title="Sachin GIDC Industrial Water Supply Rationing",
                description="Irrigation canal maintenance reduces industrial water intake to Sachin GIDC textile processing and bleaching mills.",
                source="Gujarat Water Authority",
                event_type="utility_disruption",
                location="Sachin GIDC, Surat, India",
                severity=3,
                status="active",
            ),
            Event(
                title="NH-48 Surat-Mumbai Freight Corridor Transport Congestion",
                description="Heavy multi-axle vehicle congestion at Manor toll plaza delays express logistics trucks carrying finished garment consignments.",
                source="National Highway Bulletin",
                event_type="logistics_disruption",
                location="NH-48 Corridor, India",
                severity=3,
                status="active",
            ),
            Event(
                title="Raw Silk & Georgette Yarn Price Surge",
                description="Upstream polyester and silk yarn raw material spikes raise procurement lead times across local weaving and trading units.",
                source="Textile Express",
                event_type="cost_disruption",
                location="Surat, India",
                severity=2,
                status="active",
            ),
        ]

        db.add_all(events)
        db.flush()

        # ---------------------------------------------------------
        # SUPPLIERS (Mohilya Couture Verified Surat Vendors)
        # ---------------------------------------------------------

        suppliers = [
            Supplier(
                name="Ring Road Textile Market Fabric Traders",
                country="India",
                industry="Textiles & Fabrics",
            ),
            Supplier(
                name="Puna Patiya-Godadara Rayon Fabric Traders",
                country="India",
                industry="Rayon & Silk",
            ),
            Supplier(
                name="Pandesara GIDC Dyeing & Digital Print Units",
                country="India",
                industry="Dyeing & Processing",
            ),
            Supplier(
                name="Sachin GIDC Dyeing & Printing Units",
                country="India",
                industry="Dyeing & Printing",
            ),
            Supplier(
                name="Udhna Embroidery & Digital Print Units",
                country="India",
                industry="Embroidery Job-work",
            ),
            Supplier(
                name="Bhagal-Salabatpura Lace & Trims Traders",
                country="India",
                industry="Laces & Trims",
            ),
            Supplier(
                name="Ring Road Garment Accessories Traders",
                country="India",
                industry="Buttons & Latkan",
            ),
            Supplier(
                name="Surat Thread & Embroidery Yarn Traders",
                country="India",
                industry="Yarn & Thread",
            ),
        ]

        db.add_all(suppliers)
        db.flush()

        # ---------------------------------------------------------
        # PRODUCTS (Mohilya Couture Garment Catalog)
        # ---------------------------------------------------------

        products = [
            Product(
                name="Embroidered Kurta Palazzo Dupatta Set",
                category="Ethnic Wear",
                supplier_id=suppliers[0].id,
            ),
            Product(
                name="Round Kurti Pant Dupatta Set",
                category="Ethnic Wear",
                supplier_id=suppliers[0].id,
            ),
            Product(
                name="A-Line Kurti Set",
                category="Ethnic Wear",
                supplier_id=suppliers[1].id,
            ),
            Product(
                name="Anarkali Set",
                category="Ethnic Wear",
                supplier_id=suppliers[2].id,
            ),
            Product(
                name="Embroidered Co-ord Set",
                category="Co-ord Set",
                supplier_id=suppliers[4].id,
            ),
            Product(
                name="Designer Gown",
                category="Gown",
                supplier_id=suppliers[0].id,
            ),
            Product(
                name="Indo-Western Fusion Set",
                category="Indo Western",
                supplier_id=suppliers[5].id,
            ),
            Product(
                name="Lehenga Set",
                category="Ethnic Wear",
                supplier_id=suppliers[3].id,
            ),
        ]

        db.add_all(products)
        db.flush()

        # ---------------------------------------------------------
        # SUPPLY CHAIN RELATIONSHIPS (Mohilya Couture Impact Links)
        # ---------------------------------------------------------

        links = [
            # Ring Road Flooding -> Ring Road Traders -> Kurta & Kurti sets
            SupplyChainLink(
                event_id=events[0].id,
                supplier_id=suppliers[0].id,
                product_id=products[0].id,
                relationship_type="affected",
                impact_level="high",
                estimated_delay_days=7,
            ),
            SupplyChainLink(
                event_id=events[0].id,
                supplier_id=suppliers[0].id,
                product_id=products[1].id,
                relationship_type="affected",
                impact_level="high",
                estimated_delay_days=6,
            ),
            SupplyChainLink(
                event_id=events[0].id,
                supplier_id=suppliers[0].id,
                product_id=products[5].id,
                relationship_type="affected",
                impact_level="medium",
                estimated_delay_days=5,
            ),

            # Pandesara Power Cuts -> Pandesara Dyeing -> Anarkali & Kurta
            SupplyChainLink(
                event_id=events[1].id,
                supplier_id=suppliers[2].id,
                product_id=products[3].id,
                relationship_type="affected",
                impact_level="high",
                estimated_delay_days=5,
            ),
            SupplyChainLink(
                event_id=events[1].id,
                supplier_id=suppliers[4].id,
                product_id=products[4].id,
                relationship_type="affected",
                impact_level="high",
                estimated_delay_days=6,
            ),

            # Bhagal Lace Strike -> Lace Traders -> Indo-Western & Kurta
            SupplyChainLink(
                event_id=events[2].id,
                supplier_id=suppliers[5].id,
                product_id=products[6].id,
                relationship_type="affected",
                impact_level="medium",
                estimated_delay_days=4,
            ),
            SupplyChainLink(
                event_id=events[2].id,
                supplier_id=suppliers[6].id,
                product_id=products[0].id,
                relationship_type="affected",
                impact_level="medium",
                estimated_delay_days=3,
            ),

            # Sachin GIDC Water Rationing -> Sachin Dyeing -> Lehenga & Kurti
            SupplyChainLink(
                event_id=events[3].id,
                supplier_id=suppliers[3].id,
                product_id=products[7].id,
                relationship_type="affected",
                impact_level="medium",
                estimated_delay_days=4,
            ),
            SupplyChainLink(
                event_id=events[3].id,
                supplier_id=suppliers[1].id,
                product_id=products[2].id,
                relationship_type="affected",
                impact_level="low",
                estimated_delay_days=2,
            ),

            # NH-48 Expressway Logistics -> Outbound Kurta & Gowns
            SupplyChainLink(
                event_id=events[4].id,
                supplier_id=suppliers[0].id,
                product_id=products[5].id,
                relationship_type="affected",
                impact_level="medium",
                estimated_delay_days=3,
            ),

            # Raw Yarn Surge -> Cost impact on Yarn & Thread
            SupplyChainLink(
                event_id=events[5].id,
                supplier_id=suppliers[7].id,
                product_id=products[0].id,
                relationship_type="cost_impact",
                impact_level="low",
                estimated_delay_days=2,
            ),
        ]

        db.add_all(links)
        db.commit()

        print("Mohilya Couture database seeded successfully.")
        print(f"Events: {len(events)}")
        print(f"Suppliers: {len(suppliers)}")
        print(f"Products: {len(products)}")
        print(f"Relationships: {len(links)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()