"""Web push notifications via VAPID."""
import asyncio
import json as json_lib
import logging

from pywebpush import webpush, WebPushException

from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS_SUB
from database import db

logger = logging.getLogger(__name__)


async def send_push_to_user(user_id: str, payload: dict) -> None:
    """Deliver a web-push payload to every subscription attached to this user."""
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        logger.warning("VAPID keys not configured; skipping push")
        return
    subs = await db.push_subscriptions.find(
        {"user_id": user_id}, {"_id": 0}
    ).to_list(100)
    if not subs:
        logger.info(f"No push subscriptions for user {user_id}")
        return

    successes, dead = 0, []
    for sub in subs:
        try:
            await asyncio.to_thread(
                webpush,
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=json_lib.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_SUB},
            )
            successes += 1
        except WebPushException as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (404, 410):
                dead.append(sub["endpoint"])
            logger.error(f"Push to {sub['endpoint'][:60]}... failed: {e}")
        except Exception as e:
            logger.error(f"Push error: {e}")

    if dead:
        await db.push_subscriptions.delete_many({"endpoint": {"$in": dead}})
    logger.info(
        f"Push to user {user_id}: {successes}/{len(subs)} delivered, {len(dead)} pruned"
    )
