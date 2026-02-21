import asyncio

import httpx


async def validate_e2e():
    print("Testing E2E Flow...")

    # 1. Login to get token
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        login_res = await client.post("/api/v1/auth/login", json={
            "email": "admin@veriqko.com",
            "password": "admin123!"
        })
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.text}")
            return

        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get device ID
        print("Fetching /api/v1/admin/devices...")
        devices_res = await client.get("/api/v1/admin/devices", headers=headers)
        if devices_res.status_code != 200:
            print(f"Fetch devices failed ({devices_res.status_code}): {devices_res.text}")
            return

        devices = devices_res.json()
        if not devices:
            print("No devices found. Run seed script first.")
            return
        device_id = devices[0]["id"]

        # 3. Create a new job
        print(f"Creating job for device {device_id}...")
        sn = "E2E-TEST-999"
        create_res = await client.post("/api/v1/jobs", headers=headers, json={
            "device_id": device_id,
            "serial_number": sn,
            "intake_condition": {"cosmetic": "Grade A"}
        })
        if create_res.status_code != 201:
            print(f"Job creation failed: {create_res.text}")
            return

        print(f"Job created: {sn}")

        # 4. Check dashboard
        print("Checking dashboard for SLA status...")
        stats_res = await client.get("/api/v1/stats/dashboard", headers=headers)
        recent = stats_res.json()["recent_activity"]

        test_job = next((j for j in recent if j["serial_number"] == sn), None)
        if test_job:
            print("✅ Job found in recent activity!")
            print(f"SLA Status: {test_job.get('sla_status')}")
            if test_job.get('sla_status') == 'healthy':
                print("✅ SLA status is correct (healthy for new job)")
            else:
                print(f"❌ Unexpected SLA status: {test_job.get('sla_status')}")
        else:
            print("❌ Job NOT found in recent activity!")

if __name__ == "__main__":
    asyncio.run(validate_e2e())
