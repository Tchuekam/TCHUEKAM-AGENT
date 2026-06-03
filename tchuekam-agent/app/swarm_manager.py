import os
import time
import logging
import concurrent.futures
from typing import List, Dict, Any, Optional

from mini_swe_runner import MiniSWERunner

logger = logging.getLogger(__name__)

class SwarmManager:
    """
    Orchestrates multiple MiniSWERunner instances in parallel.
    Capable of "sparking" up to N agents (default 10) simultaneously.
    """
    
    def __init__(
        self,
        num_agents: int = 10,
        model: str = "anthropic/claude-sonnet-4.6",
        env_type: str = "local",
        base_cwd: str = "/tmp/tchuekam_swarm",
        max_iterations: int = 15,
        verbose: bool = False,
        dry_run: bool = False,
    ):
        self.num_agents = num_agents
        self.model = model
        self.env_type = env_type
        self.base_cwd = base_cwd
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.dry_run = dry_run
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - [SWARM] %(levelname)s - %(message)s'
        )

        
    def _run_single_agent(self, agent_id: int, prompt: str) -> Dict[str, Any]:
        """
        Runs a single MiniSWERunner instance.
        """
        # Create isolated workspace for this agent
        agent_cwd = os.path.join(self.base_cwd, f"agent_{agent_id}")
        os.makedirs(agent_cwd, exist_ok=True)
        
        logger.info(f"Agent {agent_id} sparking in {agent_cwd}...")
        
        if self.dry_run:
            # Simulate a successful run without invoking MiniSWERunner
            logger.info(f"Agent {agent_id} dry‑run simulated success in {agent_cwd}")
            return {
                "agent_id": agent_id,
                "status": "success",
                "trajectory_file": None,
                "duration": 0,
                "cwd": agent_cwd,
                "dry_run": True,
            }
        
        try:
            runner = MiniSWERunner(
                model=self.model,
                env_type=self.env_type,
                cwd=agent_cwd,
                max_iterations=self.max_iterations,
                verbose=self.verbose
            )
            
            # Start the execution loop
            start_time = time.time()
            result_file = runner.run(prompt)
            duration = time.time() - start_time
            
            logger.info(f"Agent {agent_id} completed in {duration:.2f}s. Result saved to {result_file}")
            
            return {
                "agent_id": agent_id,
                "status": "success",
                "trajectory_file": result_file,
                "duration": duration,
                "cwd": agent_cwd
            }
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {e}", exc_info=True)
            return {
                "agent_id": agent_id,
                "status": "error",
                "error": str(e),
                "cwd": agent_cwd
            }

    def spark(self, prompts: List[str]) -> List[Dict[str, Any]]:
        """
        Launch the swarm! 
        Given a list of prompts (one per agent), run them all concurrently.
        If there are fewer prompts than num_agents, we only spark that many agents.
        If there is 1 prompt but multiple agents, we can theoretically assign the same prompt or variations.
        For now, this assumes a list of distinct sub-tasks.
        """
        tasks_to_run = min(len(prompts), self.num_agents)
        logger.info(f"⚡ Sparking {tasks_to_run} agents in parallel ⚡")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_agents) as executor:
            future_to_agent = {
                executor.submit(self._run_single_agent, i, prompts[i]): i 
                for i in range(tasks_to_run)
            }
            
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_id = future_to_agent[future]
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    logger.error(f"Agent {agent_id} generated an unhandled exception: {exc}")
                    results.append({"agent_id": agent_id, "status": "critical_error", "error": str(exc)})
                    
        return sorted(results, key=lambda x: x.get("agent_id", 0))
