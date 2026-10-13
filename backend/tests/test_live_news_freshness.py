from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from app.services.news_ingestion_service import NewsIngestionService
from app.core.database import SessionLocal

def test_article_date_parsing_and_freshness_cutoff():
    db = SessionLocal()
    try:
        service = NewsIngestionService(db, user_id=8)
        now_utc = datetime.now(timezone.utc)

        # 1. Fresh date (5 hours ago)
        fresh_dt = now_utc - timedelta(hours=5)
        fresh_str = format_datetime(fresh_dt)
        parsed_dt, iso_str = service.parse_article_date(fresh_str)
        assert parsed_dt is not None
        assert abs((now_utc - parsed_dt).total_seconds() - 5 * 3600) < 60

        # 2. Old date (5 months ago - e.g. June 2026)
        old_dt = now_utc - timedelta(days=120)
        old_str = format_datetime(old_dt)
        old_parsed, _ = service.parse_article_date(old_str)
        assert old_parsed is not None

        # 3. Test relevance evaluation with old date (even if garment related)
        context = {
            "company_name": "Mohilya Couture Private Limited",
            "industry": "Garment",
            "cities": ["Surat", "Pandesara"],
            "supplier_names": ["Ring Road Textile Market Fabric Traders"],
            "components": ["Fabric Rolls"],
        }
        res_old = service.evaluate_business_relevance(
            title="Surat textile market fire breaks out",
            description="Major fire in Surat textile market",
            context=context,
            pub_dt=old_parsed,
        )
        assert res_old["is_relevant"] is False
        assert "72h freshness limit" in res_old["explanation"]

        # 4. Test fresh garment disruption (5 hours ago)
        res_fresh = service.evaluate_business_relevance(
            title="Surat Pandesara GIDC industrial fire halts fabric dyeing",
            description="Major fire in Pandesara GIDC fabric dyeing plant halts dispatch",
            context=context,
            pub_dt=fresh_dt,
        )
        assert res_fresh["is_relevant"] is True
        assert res_fresh["relevance_score"] >= 80

        # 5. Strict rejection of DRDO missile test
        res_drdo = service.evaluate_business_relevance(
            title="DRDO successfully flight-tests Man Portable Anti-Tank Guided Missile",
            description="Defense trial conducted at test range with top attack capability",
            context=context,
            pub_dt=fresh_dt,
        )
        assert res_drdo["is_relevant"] is False

        # 6. Strict rejection of electronics showroom fire for Garment
        res_electronics_fire = service.evaluate_business_relevance(
            title="Major fire at electronics showroom in Mumbai",
            description="Fire damages multi-storey electronics showroom and warehouse",
            context=context,
            pub_dt=fresh_dt,
        )
        assert res_electronics_fire["is_relevant"] is False
        assert "Irrelevant to garment/textile" in res_electronics_fire["explanation"]

        # 7. Strict rejection of wafer fab delay for Garment
        res_wafer = service.evaluate_business_relevance(
            title="Tata's Gujarat wafer fab reportedly faces fresh delay, clouding chipmaking ambitions",
            description="Semiconductor plant timeline delayed due to tool deliveries",
            context=context,
            pub_dt=fresh_dt,
        )
        assert res_wafer["is_relevant"] is False
        assert "Irrelevant to garment/textile" in res_wafer["explanation"]

        # 8. Non-disruption news (speech/award) rejected
        res_speech = service.evaluate_business_relevance(
            title="Textile Minister praises trainees at Surat fashion institute",
            description="Minister gives certificate to successful designers",
            context=context,
            pub_dt=fresh_dt,
        )
        assert res_speech["is_relevant"] is False
        assert "Not an operational disruption" in res_speech["explanation"]
    finally:
        db.close()
