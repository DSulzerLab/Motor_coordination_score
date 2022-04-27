## 
## mouse_coordination_score.py
## Mice Motor Coordination
##
## Compute coordination score based on statistical analysis data
## generated from mouse_metrics.py
##

from contextlib import ExitStack
import numpy as np
from scipy import stats
import pandas as pd
import h5py
import matplotlib.pyplot as plt

## Compute paw stability metric
## steplengths: Array containing average step lengths for a certain treadmill speed
## value      : A single element from the steplengths array 
def paw_stability(steplengths, value):
    ## Compute median of average step length data
    median = np.median(steplengths)

    ## Compute distance of step length from median
    if value < median:
        center = np.count_nonzero(steplengths < median)
        left = np.count_nonzero(steplengths < value)
        stability = np.abs(left - center)
    else:
        center = np.count_nonzero(steplengths > median)
        right = np.count_nonzero(steplengths > value)
        stability = np.abs(right - center)
    
    ## Normalize from 0 to 100
    stability /= center
    return (1 - stability) * 100

def main():
    ## Import mice metrics from file
    with ExitStack() as stack:
        ## Import analyzed mice data and mice metrics
        mice_data    = stack.enter_context(h5py.File('mice_data.hdf5', 'a'))
        mice_metrics = stack.enter_context(h5py.File('mice_metrics.hdf5', 'a'))
        
        ## Extract metrics keys into matrices
        ## Probability and expectation of quadrant
        ## Used to determine mouse head's expected position in box
        ## If expectation is closer to 1, motor coordination is better 
        expectation = mice_metrics['expectation'][...]

        ## Y axis standard deviation (SD)
        ## Used to determine whether mouse moves sideways on treadmill
        ## If SD is smaller, motor coordination is better
        sd = mice_metrics['sd'][...]

        ## Step length mean
        ## Used to determine whether mouse is actually moving or staying in place
        ## If step length is larger, motor coordination is better        
        lfp_steplength = mice_metrics['lfp_steplength'][...] # Left Front Paw Step Length Mean
        rfp_steplength = mice_metrics['rfp_steplength'][...] # Right Front Paw Step Length Mean
        lhp_steplength = mice_metrics['lhp_steplength'][...] # Left Hind Paw Step Length Mean
        rhp_steplength = mice_metrics['rhp_steplength'][...] # Right Hind Paw Step Length Mean

        ## Get mice data keys from hdf5 file
        mice_keys = list(mice_data.keys())
        
        ## Declare matrix for raw weighted average scores
        ## Weighted average is computed using percentiles of each metrics
        ## 40% for expectation of mouse quadrant, 40% for Y axis SD, 5% for each paw step length
        coordination_weights = np.array([40.0, 40.0, 5.0, 5.0, 5.0, 5.0])
        raw_scores = np.zeros((len(mice_keys), 5, 12))

        ## Compute weighted average scores for each mouse
        for index1, mouse in enumerate(mice_keys):
            day_keys = mice_data[mouse].keys()

            ## Compute weighted average scores for each mouse on each day
            for index2, day in enumerate(day_keys):
                intermediate_scores = np.zeros((5, 6)) # (Number of treadmill speeds x number of metrics)
                ## Extract metrics for mouse on specific day
                key  = mouse + '/' + day + '/' + 'metrics'
                data = mice_data[key][...]
                ## Compute percentiles for each metric
                for i in range(5):
                    ## Step 1: Percentile of mouse quadrant
                    ## 100 - percentile is used because smaller expectation is better
                    intermediate_scores[i, 0] = 100 - stats.percentileofscore(expectation[i], data[i, 0])
                    ## Step 2: Percentile of SD
                    ## 100 - percentile is used because smaller SD is better
                    intermediate_scores[i, 1] = 100 - stats.percentileofscore(sd[i], data[i, 1])
                    ## Step 3: Paw stability
                    intermediate_scores[i, 2] = paw_stability(lfp_steplength[i], data[i, 2])
                    intermediate_scores[i, 3] = paw_stability(rfp_steplength[i], data[i, 3])
                    intermediate_scores[i, 4] = paw_stability(lhp_steplength[i], data[i, 4])
                    intermediate_scores[i, 5] = paw_stability(rhp_steplength[i], data[i, 5])

                ## Step 4: Weighted average
                raw_scores[index1, :, index2] = np.average(intermediate_scores, axis = 1, weights = coordination_weights)
        
        ## Flatten weighted average scores matrix into 1 dimension for computing percentiles
        raw_scores_merged = raw_scores.flatten()
        row_names = ['3m/min', '6m/min', '8m/min', '10m/min', '12m/min']
        coordination_scores_matrix = None
        ## Compute coordination score for each mouse
        for index, mouse in enumerate(mice_keys):
            
            ## Declare matrix for coordination scores
            ## Coordination score is computed using percentiles of weighted average score
            day_keys = mice_data[mouse].keys()
            coordination_scores = np.zeros((5, len(day_keys)))

            ## Compute coordination score for each mouse on each day
            for i in range(5):
                for j in range(len(day_keys)):
                    # Compute percentile for weighted average score
                    percentile = stats.percentileofscore(raw_scores_merged, raw_scores[index, i, j])
                    # Rescale coordination score from 1 to 5
                    if percentile < 100:
                        coordination_scores[i, j] = int(percentile / 20) + 1
                    else:
                        coordination_scores[i, j] = 5
            
            ## Convert to Pandas frame with row/column names for clarity
            ## Export frame to CSV
            coordination_scores_frame = pd.DataFrame(data = coordination_scores, index = row_names, columns = day_keys)
            coordination_scores_frame.to_csv(mouse + '_coordination_scores.csv')

            ## Store coordination scores in matrix
            if coordination_scores_matrix is None:
                coordination_scores_matrix = coordination_scores
            else:
                coordination_scores_matrix = np.vstack((coordination_scores_matrix, coordination_scores))
        
        ## Compute mean and standard error of coordination scores over 12 days
        coordination_score_means = np.mean(coordination_scores_matrix, axis = 0)
        coordination_score_error = stats.sem(coordination_scores_matrix, axis = 0)

        ## Plot results
        plt.errorbar(range(1, 13), coordination_score_means, yerr = coordination_score_error, marker = 'o', capsize = 4)
        plt.xticks(range(1, 13))
        plt.yticks(range(6))
        plt.xlabel('Day')
        plt.ylabel('Average Coordination Score')
        plt.tight_layout()
        plt.savefig('coordinationscore.png', dpi = 300)
        plt.show()

main()
