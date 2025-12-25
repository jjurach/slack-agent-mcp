#!/usr/bin/env python3
"""
Milestone notifications example for slack-notifications.

This script demonstrates how to integrate Slack notifications
into a typical application workflow with milestone tracking.
"""

import asyncio
import time
from slack_notifications import notify_milestone, notify_milestone_async

def simulate_application_startup():
    """Simulate application startup with milestone notifications."""

    print("🚀 Starting application...")

    # Application initialization milestones
    notify_milestone("Application startup initiated", level="info")

    time.sleep(0.5)  # Simulate some work
    notify_milestone("Configuration loaded successfully", level="success")

    time.sleep(0.5)
    notify_milestone("Database connection established", level="success")

    time.sleep(0.5)
    notify_milestone("Cache initialized", level="success")

    notify_milestone("Application startup completed - ready to serve requests!", level="success")

def simulate_data_processing():
    """Simulate data processing with progress notifications."""

    print("\n📊 Starting data processing pipeline...")

    notify_milestone("Data processing pipeline started", level="info")

    # Simulate processing steps
    steps = [
        ("Data validation completed", "success"),
        ("Duplicate records removed", "info"),
        ("Data transformation applied", "success"),
        ("Quality checks passed", "success"),
        ("Results exported successfully", "success")
    ]

    for step_message, level in steps:
        time.sleep(0.3)  # Simulate processing time
        notify_milestone(step_message, level=level)

    notify_milestone("Data processing pipeline completed!", level="success")

def simulate_error_handling():
    """Simulate error scenarios with appropriate notifications."""

    print("\n⚠️  Testing error handling...")

    notify_milestone("Starting automated test suite", level="info")

    try:
        # Simulate a warning condition
        time.sleep(0.2)
        notify_milestone("Warning: API response time above threshold", level="warning")

        # Simulate an error condition
        time.sleep(0.2)
        # In a real scenario, this might be caught and reported
        notify_milestone("Error: Database connection timeout", level="error")

        # Recovery notification
        time.sleep(0.2)
        notify_milestone("Recovery: Fallback database connection established", level="success")

    except Exception as e:
        notify_milestone(f"Critical failure in test suite: {e}", level="error")

    notify_milestone("Test suite completed with error handling validation", level="info")

async def simulate_async_operations():
    """Simulate async operations with concurrent notifications."""

    print("\n🔄 Testing async notifications...")

    notify_milestone("Async operations test started", level="info")

    # Run multiple async notifications concurrently
    tasks = [
        notify_milestone_async("Background task 1 completed", level="success"),
        notify_milestone_async("Background task 2 completed", level="success"),
        notify_milestone_async("Background task 3 completed", level="success"),
    ]

    # Wait for all async notifications to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check results
    success_count = sum(1 for r in results if not isinstance(r, Exception))
    error_count = len(results) - success_count

    if error_count == 0:
        notify_milestone(f"All {success_count} async notifications sent successfully", level="success")
    else:
        notify_milestone(f"Async notifications: {success_count} success, {error_count} errors", level="warning")

def demonstrate_channel_routing():
    """Demonstrate routing notifications to different channels."""

    print("\n📢 Testing channel routing...")

    # Different types of notifications go to different channels
    notifications = [
        ("System health check passed", "#health", "success"),
        ("Security scan completed", "#security", "info"),
        ("Performance metrics updated", "#metrics", "info"),
        ("Backup completed successfully", "#backups", "success"),
        ("Alert: High CPU usage detected", "#alerts", "warning"),
    ]

    for message, channel, level in notifications:
        notify_milestone(message, channel=channel, level=level)
        time.sleep(0.1)  # Small delay between notifications

    notify_milestone("Channel routing test completed", level="info")

def main():
    """Run all milestone notification demonstrations."""

    print("🎯 Slack Notifications - Milestone Examples")
    print("=" * 50)

    try:
        # Synchronous examples
        simulate_application_startup()
        simulate_data_processing()
        simulate_error_handling()
        demonstrate_channel_routing()

        # Asynchronous example
        asyncio.run(simulate_async_operations())

        print("\n" + "=" * 50)
        print("✅ All milestone notification examples completed!")
        print("\nNote: Make sure your SLACK_BOT_TOKEN environment variable is set")
        print("and your Slack app has the necessary permissions and channel access.")

    except Exception as e:
        print(f"\n❌ Example failed with error: {e}")
        print("Make sure you have:")
        print("1. Set SLACK_BOT_TOKEN environment variable")
        print("2. Slack app with chat:write permission")
        print("3. Bot added to the target channels")

if __name__ == "__main__":
    main()