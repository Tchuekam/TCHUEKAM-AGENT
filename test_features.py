import os, sys

# Ensure the agent package is on the import path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "tchuekam-agent", "app")))

# Test SwarmManager

def test_swarm():
    try:
        from swarm_manager import SwarmManager
        manager = SwarmManager(num_agents=2, base_cwd=os.path.join(os.getcwd(), ".swarm_test"), dry_run=True)
        prompts = ["Echo 1", "Echo 2"]
        results = manager.spark(prompts)
        print("Swarm results:", results)
    except Exception as e:
        print("Swarm error:", e)

# Test browser_click_coords registration and execution

def test_browser_click_coords():
    try:
        from tools.browser_tool import _BROWSER_SCHEMA_MAP, browser_click_coords
        print("browser_click_coords schema:", _BROWSER_SCHEMA_MAP.get("browser_click_coords"))
        result = browser_click_coords(100, 200)
        print("browser_click_coords result:", result)
    except Exception as e:
        print("Browser click_coords error:", e)

if __name__ == "__main__":
    test_swarm()
    test_browser_click_coords()
