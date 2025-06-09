from apscheduler.schedulers.asyncio import AsyncIOScheduler
from notifications import check_and_notify_at_risk_customers_for_all_users

def start_scheduler(application):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_notify_at_risk_customers_for_all_users,
        'interval',
        minutes=1, # Test
        kwargs={"context": application.bot}
    )
    scheduler.start()
    print("✅ Scheduler started.")
