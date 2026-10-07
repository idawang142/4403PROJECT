# Boundary validation

The original four smoke tests are retained. Nine additional test executions cover seven boundary categories (three budgets are used for the hub test).

| Case | Expected result |
|---|---|
| Isolated susceptible node | No new infections or contact cost; isolated-node fear update stays finite and zero without a signal. |
| Complete graph, N=10, beta=1 | With one initial infection and gamma=0, everyone has been infected after one step; cumulative_size is 1 and final_size is unavailable until extinction. |
| Observation alpha=0 | Output arrays and numerical summaries exactly match rule=none for the same seed; fear/caution remains zero. |
| Observation delta=1 | Previous fear vanishes; new infected-neighbour input remains. With no new signal, fear becomes zero. |
| Threshold equality | Fear equal to theta is not cautious; slightly greater fear is cautious. |
| Time cap | beta=gamma=0 terminates after exactly max_steps with unchanged cumulative infected fraction; extinct is false and final_size is NaN. |
| Hub saturation | For N=20, hub_frac=0.1, budgets 0.1/0.5/1.0 target exactly the selected two highest-degree nodes. |

The original engine recorded 13 passed checks. The current suite also tests
explicit unfinished-run status, cost timing, degree accounting, cache provenance,
initial innovators, sparse/dense equivalence and deterministic hub ties. One clarification: the delta=1 test verifies that old fear is cleared while new infection signals can still generate fear, consistent with the current model.
