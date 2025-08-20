"""
Forex Market Scheduler Service
Manages background tasks aligned with 24/5 forex market sessions.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from .data_service import DataService
from .signal_service import SignalService


class ForexSchedulerService:
    """
    Background task scheduler for 24/5 forex market operations.
    
    Market Hours (EST):
    - Sydney: Sunday 5:00 PM → Monday 4:00 PM  
    - Tokyo: Sunday 7:00 PM → Monday 4:00 AM
    - London: Monday 3:00 AM → Monday 12:00 PM
    - New York: Monday 8:00 AM → Monday 5:00 PM
    
    Continuous operation: Sunday 5 PM EST → Friday 5 PM EST
    """

    def __init__(self, data_service: DataService, signal_service: SignalService):
        self.data_service = data_service
        self.signal_service = signal_service
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self.is_running = False
        
        # Track last signal generation for each pair
        self.last_signals: Dict[str, datetime] = {}
        
        # Market session times (in UTC for consistency)
        self.market_sessions = {
            'sydney': {'start': 22, 'end': 21},    # 22:00 UTC Sunday → 21:00 UTC Monday
            'tokyo': {'start': 0, 'end': 9},       # 00:00 UTC Monday → 09:00 UTC Monday  
            'london': {'start': 8, 'end': 17},     # 08:00 UTC → 17:00 UTC
            'new_york': {'start': 13, 'end': 22}   # 13:00 UTC → 22:00 UTC
        }
        
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup scheduler event listeners for monitoring."""
        def job_listener(event):
            if event.exception:
                logging.error(f"📅 Scheduled job failed: {event.job_id} - {event.exception}")
            else:
                logging.info(f"📅 Scheduled job completed: {event.job_id}")

        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    async def start_scheduler(self):
        """Start the forex market scheduler."""
        if self.is_running:
            logging.warning("📅 Scheduler already running")
            return

        logging.info("🚀 Starting Forex Market Scheduler...")
        
        # Add market-aware jobs
        await self._schedule_market_jobs()
        
        self.scheduler.start()
        self.is_running = True
        
        logging.info("✅ Forex Market Scheduler started successfully")
        await self._log_next_jobs()

    async def stop_scheduler(self):
        """Stop the scheduler gracefully."""
        if not self.is_running:
            return

        logging.info("⏹️ Stopping Forex Market Scheduler...")
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logging.info("✅ Scheduler stopped")

    async def _schedule_market_jobs(self):
        """Schedule jobs based on forex market sessions."""
        
        # 1. High-frequency during major overlaps (London-NY: 8AM-12PM EST / 13:00-17:00 UTC)
        self.scheduler.add_job(
            func=self._generate_all_signals_high_freq,
            trigger=IntervalTrigger(minutes=5),
            id='high_freq_signals',
            name='High Frequency Signals (London-NY Overlap)',
            max_instances=1,
            replace_existing=True
        )
        
        # 2. Standard frequency during active sessions
        self.scheduler.add_job(
            func=self._generate_all_signals_standard,
            trigger=IntervalTrigger(minutes=15),
            id='standard_freq_signals', 
            name='Standard Frequency Signals (Active Sessions)',
            max_instances=1,
            replace_existing=True
        )
        
        # 3. Low frequency during quiet periods
        self.scheduler.add_job(
            func=self._generate_all_signals_low_freq,
            trigger=IntervalTrigger(hours=1),
            id='low_freq_signals',
            name='Low Frequency Signals (Quiet Periods)', 
            max_instances=1,
            replace_existing=True
        )
        
        # 4. Market open signals (Sunday 5 PM EST / 22:00 UTC)
        self.scheduler.add_job(
            func=self._market_open_signals,
            trigger=CronTrigger(day_of_week=0, hour=22, minute=0),  # Sunday 22:00 UTC
            id='market_open',
            name='Market Open Signals (Sunday)',
            max_instances=1,
            replace_existing=True
        )
        
        # 5. Market close signals (Friday 5 PM EST / 22:00 UTC)
        self.scheduler.add_job(
            func=self._market_close_signals,
            trigger=CronTrigger(day_of_week=4, hour=22, minute=0),  # Friday 22:00 UTC
            id='market_close',
            name='Market Close Signals (Friday)',
            max_instances=1,
            replace_existing=True
        )
        
        # 6. Health check every hour
        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(hours=1),
            id='health_check',
            name='System Health Check',
            max_instances=1,
            replace_existing=True
        )

    def _is_major_overlap(self) -> bool:
        """Check if current time is during London-NY overlap (high volatility)."""
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        current_weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
        
        # Monday-Friday, 13:00-17:00 UTC (8AM-12PM EST)
        return (0 <= current_weekday <= 4) and (13 <= current_hour < 17)

    def _is_market_active(self) -> bool:
        """Check if any major forex session is currently active."""
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        current_weekday = now_utc.weekday()
        
        # Weekend check (Saturday = 5, Sunday before 22:00 = 6)
        if current_weekday == 5:  # Saturday
            return False
        if current_weekday == 6 and current_hour < 22:  # Sunday before 22:00 UTC
            return False
        if current_weekday == 4 and current_hour >= 22:  # Friday after 22:00 UTC
            return False
            
        # Market is active 24/5: Sunday 22:00 UTC → Friday 22:00 UTC
        return True

    async def _generate_all_signals_high_freq(self):
        """Generate signals during high-frequency periods (major overlaps)."""
        if not self._is_major_overlap():
            return
            
        logging.info("🔥 High-frequency signal generation (London-NY overlap)")
        await self._execute_signal_generation("HIGH_FREQ")

    async def _generate_all_signals_standard(self):
        """Generate signals during standard market hours."""
        if not self._is_market_active() or self._is_major_overlap():
            return
            
        logging.info("📊 Standard frequency signal generation")
        await self._execute_signal_generation("STANDARD")

    async def _generate_all_signals_low_freq(self):
        """Generate signals during quiet periods."""
        if self._is_market_active():
            return
            
        logging.info("😴 Low frequency signal generation (quiet period)")
        await self._execute_signal_generation("LOW_FREQ")

    async def _market_open_signals(self):
        """Generate signals at market open (Sunday 5 PM EST)."""
        logging.info("🌅 Market Open - Generating fresh signals for the week")
        await self._execute_signal_generation("MARKET_OPEN")

    async def _market_close_signals(self):
        """Generate final signals at market close (Friday 5 PM EST).""" 
        logging.info("🌅 Market Close - Generating final signals for the week")
        await self._execute_signal_generation("MARKET_CLOSE")

    async def _execute_signal_generation(self, frequency_type: str):
        """Execute signal generation with error handling."""
        try:
            # Get fresh market data
            all_price_data = await self.data_service.get_historical_data_for_all_pairs()
            
            # Generate signals for all pairs
            signals = await self.signal_service.generate_signals_for_all_pairs(all_price_data)
            
            # Track generation time
            generation_time = datetime.now(timezone.utc)
            for signal in signals:
                self.last_signals[signal.pair] = generation_time
            
            logging.info(
                f"✅ [{frequency_type}] Generated {len(signals)} signals at {generation_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
        except Exception as e:
            logging.error(f"❌ [{frequency_type}] Signal generation failed: {e}")

    async def _health_check(self):
        """Periodic health check of services."""
        try:
            # Check OANDA connection
            health_status = await self.data_service.health_check()
            
            # Check signal service
            signal_count = len(self.last_signals)
            
            current_time = datetime.now(timezone.utc)
            market_status = "ACTIVE" if self._is_market_active() else "CLOSED"
            overlap_status = "HIGH_VOLATILITY" if self._is_major_overlap() else "NORMAL"
            
            logging.info(
                f"💚 Health Check - OANDA: {health_status['status']}, "
                f"Signals: {signal_count} pairs tracked, "
                f"Market: {market_status}, "
                f"Period: {overlap_status}, "
                f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
        except Exception as e:
            logging.error(f"❌ Health check failed: {e}")

    async def _log_next_jobs(self):
        """Log information about scheduled jobs."""
        if not self.scheduler.get_jobs():
            logging.warning("📅 No jobs scheduled")
            return
            
        logging.info("📅 Scheduled Jobs:")
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                logging.info(f"  • {job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status."""
        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'is_running': self.is_running,
            'market_active': self._is_market_active(),
            'major_overlap': self._is_major_overlap(),
            'jobs_count': len(jobs_info),
            'jobs': jobs_info,
            'last_signals': {
                pair: timestamp.isoformat() 
                for pair, timestamp in self.last_signals.items()
            }
        }
