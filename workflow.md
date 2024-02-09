# Workflow necessary for re-running results

UPDATE NIGHT ZERO EVERYWHERE

## Simulated observations
- Run by Sam/Jake
- Should have a folder of visit_XXXXX.h5 for all LSST observations

## Convert to digest2 input
- Use lsst_neocp.create_digest2_input to make a bunch of `filtered_visit_XXXXX.h5` and `night_XXX.obs` files (one for convenience, one for digest2)

## Run digest2
- Set up a checkpoint queue run of every .obs file

## Do current criteria analysis
- Run through the `Predictions with current criteria.ipynb` notebook

## Mitigation algorithm
We'll get there when we get there