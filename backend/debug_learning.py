#!/usr/bin/env python3
"""
Debug script for learning plans API issue
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.learning_plan import LearningPlan
from sqlalchemy import select

async def test_learning_plans_query():
    """Test the exact query that's failing in the API"""
    user_id = '8f719226-524c-4b75-adfa-84f76828562a'
    
    try:
        print(f"Testing query for user: {user_id}")
        
        async with AsyncSessionLocal() as session:
            print("✅ Database session created")
            
            # Execute the query
            result = await session.execute(
                select(LearningPlan).where(LearningPlan.user_id == user_id).order_by(LearningPlan.created_at.desc())
            )
            print("✅ Query executed")
            
            learning_plans = result.scalars().all()
            print(f"✅ Found {len(learning_plans)} learning plans")
            
            # Convert to the same format as the API
            plans = []
            for plan in learning_plans:
                plan_dict = {
                    "id": plan.id,
                    "title": plan.title,
                    "description": plan.description,
                    "content": plan.content,
                    "created_at": str(plan.created_at) if plan.created_at is not None else None
                }
                plans.append(plan_dict)
                print(f"  - Plan: {plan.title}")
            
            print(f"✅ Query successful! Returning {len(plans)} plans")
            return plans
            
    except Exception as e:
        print(f"❌ Query failed with error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("=== Debug Learning Plans Query ===")
    result = asyncio.run(test_learning_plans_query())
    print(f"Final result: {len(result)} plans") 