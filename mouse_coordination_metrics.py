##
## mouse_coordination_metrics.py
## Mouse Motor Coordination
##
## Run statistical analysis on mouse data derived from DeepLabCut
##

from contextlib import ExitStack
import os
import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import mplcursors

## Dictionary to store list of mice and corresponding files
## Main key     : mouse ID
## Secondary key: day X of mouse training
## Value        : list containing arguments for metrics() function
database = {
            'C4': {
                'd01': ["C4/d01.csv", "C4/C4-TMday01.csv", "C4/day01.png", False],
                'd02': ["C4/d02.csv", "C4/C4-TMday02.csv", "C4/day02.png", False],
                'd03': ["C4/d03.csv", "C4/C4-TMday03.csv", "C4/day03.png", False],
                'd04': ["C4/d04.csv", "C4/C4-TMday04.csv", "C4/day04.png", False],
                'd05': ["C4/d05.csv", "C4/C4-TMday05.csv", "C4/day05.png", False],
                'd06': ["C4/d06.csv", "C4/C4-TMday06.csv", "C4/day06.png", False],
                'd07': ["C4/d07.csv", "C4/C4-TMday07.csv", "C4/day07.png", False],
                'd08': ["C4/d08.csv", "C4/C4-TMday08.csv", "C4/day08.png", False],
                'd09': ["C4/d09.csv", "C4/C4-TMday09.csv", "C4/day09.png", True],
                'd10': ["C4/d10.csv", "C4/C4-TMday10.csv", "C4/day10.png", True],
                'd11': ["C4/d11.csv", "C4/C4-TMday11.csv", "C4/day11.png", True],
                'd12': ["C4/d12.csv", "C4/C4-TMday12.csv", "C4/day12.png", True],
            }
         }

## Process mouse data and return statisical metrics to be used for coordination score
## Arguments
## file   : analyzed CSV file that contains mouse paw X/Y position and step length
## rawfile: original CSV file from DeepLabCut that contains mouse head X/Y position
## corners: coordinates of box corners from video. 
##          Can either be a filepath to image or (4, 1, 2) shaped NumPy array
## reverse: Boolean flag to indicate whether mouse is running in reverse on given day 
def metrics(file, raw_file, corners = None, reverse = False):
    ## Load CSV files
    data     = pd.read_csv(file, encoding = 'cp1252')
    raw_data = pd.read_csv(raw_file, encoding = 'cp1252', skiprows = [0, 2])

    ## Extract head and paw data
    head   = raw_data[['head', 'head.1']].to_numpy()
    head   = np.hstack((head, data[['time']]))
    lf_paw = data[['lfp_x', 'lfp_y', 'lfp_steplength', 'time']].to_numpy()
    rf_paw = data[['rfp_x', 'rfp_y', 'rfp_steplength', 'time']].to_numpy()
    lh_paw = data[['lhp_x', 'lhp_y', 'lhp_steplength', 'time']].to_numpy()
    rh_paw = data[['rhp_x', 'rhp_y', 'rhp_steplength', 'time']].to_numpy()
    extracted_data = [head, lf_paw, rf_paw, lh_paw, rh_paw]

    ## Load box corner data
    box_corners  = np.zeros(4)
    bottom_left  = None
    top_left     = None
    top_right    = None
    bottom_right = None
    if (corners is None):
        ## Load box corners from DeepLabCut CSV file
        bottom_left  = raw_data[['bottomleft', 'bottomleft.1']].to_numpy()
        top_left     = raw_data[['topleft', 'topleft.1']].to_numpy()
        top_right    = raw_data[['topright', 'topright.1']].to_numpy()
        bottom_right = raw_data[['bottomright', 'bottomright.1']].to_numpy()
    elif (isinstance(corners, np.ndarray)):
        ## Copy box corners stored in hdf5 file
        bottom_left  = corners[0]
        top_left     = corners[1]
        top_right    = corners[2]
        bottom_right = corners[3]
    elif (isinstance(corners, str)):
        ## Plot image of mouse running in treadmill
        fig = plt.figure()
        img = mpimg.imread(corners)
        plt.imshow(img)

        ## Create functions to extract box corner coordinates from selected markers on image
        coordinates = []
        scatters    = []
        cursor      = mplcursors.cursor(multiple = True)

        ## Plot callback function for adding point to selection list
        @cursor.connect("add")
        def addpoint(selection):
            if len(coordinates) < 4:
                point = np.around(selection.target, decimals = 3)
                coordinates.append(point)
                text = "X = " + str(point[0]) + "\n" + "Y = " + str(point[1])
                selection.annotation.set_text(text)
            else:
                cursor.remove_selection(selection)
        
        ## Plot callback function for removing point from selection list
        @cursor.connect("remove")
        def removepoint(selection):
            point = np.around(selection.target, decimals = 3)
            val   = None
            for index, coordinate in enumerate(coordinates):
                if np.array_equal(coordinate, point):
                    val = index
                    break
            if (val != None):
                coordinates.pop(val)
                scatters[val].remove()
                scatters.pop(val)
        
        ## Plot callback to display selected points with scatter plot markers
        def pointplot(event):
            if len(coordinates) > len(scatters):
                scatters.append(plt.scatter(coordinates[-1][0], coordinates[-1][1], color = "#33BBEE"))
            fig.canvas.draw()
        
        ## Connect callback function and display image
        fig.canvas.mpl_connect('button_press_event', pointplot)
        plt.show()

        ## Display error if four box coordinates are not selected
        if len(coordinates) != 4:
            message = "You selected {number} point(s) for the box corners, but 4 are required".format(number = len(coordinates))
            raise ValueError(message)

        ## Organize coordinates array in correct order
        ## Order: bottom left, top left, top right, bottom right
        coordinates = sorted(coordinates, key = lambda x: x[0])
        if (coordinates[1][1] > coordinates[0][1]):
            coordinates[0], coordinates[1] = coordinates[1], coordinates[0]
        if (coordinates[3][1] < coordinates[2][1]):
            coordinates[2], coordinates[3] = coordinates[3], coordinates[2]
        coordinates = np.array(coordinates)
        
        ## Assign coordinates to separate variables
        bottom_left  = coordinates[[0]]
        top_left     = coordinates[[1]]
        top_right    = coordinates[[2]]
        bottom_right = coordinates[[3]]
    else:
        raise ValueError('Box corners must be either filepath to raw data, filepath to labeled frame, or list of 4 positions')
    
    ## Compute average top/bottom X/Y position using box corners
    box_coordinates = np.array([bottom_left, top_left, top_right, bottom_right])
    box_corners[0]  = (np.mean(bottom_left[:, 0]) + np.mean(top_left[:, 0])) / 2
    box_corners[1]  = (np.mean(bottom_right[:, 0]) + np.mean(top_right[:, 0])) / 2
    box_corners[2]  = (np.mean(top_left[:, 1]) + np.mean(top_right[:, 1])) / 2
    box_corners[3]  = (np.mean(bottom_left[:, 1]) + np.mean(bottom_right[:, 1])) / 2

    ## Remove outliers from each body part's X/Y data
    for i in range(len(extracted_data)):
        part = extracted_data[i]
        left_x_mask   = part[:, 0] >= box_corners[0]
        right_x_mask  = part[:, 0] <= box_corners[1]
        top_y_mask    = part[:, 1] >= box_corners[2]
        bottom_y_mask = part[:, 1] <= box_corners[3]
        extracted_data[i] = part[left_x_mask & right_x_mask & top_y_mask & bottom_y_mask]
    
    ## Normalize each body part's X/Y data with respect to box corners
    for part in extracted_data:
        part[:, 0] -= box_corners[0]
        part[:, 0] /= (box_corners[1] - box_corners[0])
        part[:, 1] -= box_corners[2]
        part[:, 1] /= (box_corners[3] - box_corners[2])
        ## Reverse coordinates to account for mouse running in reverse direction
        if reverse:
            part[:, :2] = 1 - part[:, :2]

    ## Declare specific time sections to extract from data
    ## Each section corresponds to different treadmill speed
    ## 30 - 90 seconds  : 3m/min
    ## 90 - 150 seconds : 6m/min
    ## 150 - 210 seconds: 8m/min
    ## 210 - 270 seconds: 10m/min
    ## 270 - 330 seconds: 12m/min 
    sections = np.array([30.0, 90.0, 150.0, 210.0, 270.0, 330.0])

    ## Declare mouse quadrants and position
    ## Box is split into 5 equally-sized quadrants
    ## 1 is frontmost quadrant, 5 is backmost quadrant
    quadrant_locs = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1])
    quadrants     = np.array([1, 2, 3, 4, 5])

    ## Declare mouse metrics variables
    ## Probability and expectation of quadrant
    ## Used to determine mouse head's expected position in box
    ## If expectation is closer to 1, motor coordination is better 
    quadrant_probs       = np.zeros((5, 5)) 
    quadrant_expectation = np.zeros((5, 1))

    ## Y axis standard deviation (SD)
    ## Used to determine whether mouse moves sideways on treadmill
    ## If SD is smaller, motor coordination is better
    y_axis_sd = np.zeros((5, 1))

    ## Step length mean
    ## Used to determine whether mouse is actually moving or staying in place
    ## If step length is larger, motor coordination is better
    steplength = np.zeros((5, 4))

    ## Compute mouse metrics
    for i in range(len(extracted_data)):

        ## Get indexes of 60-second sections corresponding to different treadmill speeds
        indexes = np.zeros(len(sections), dtype = np.int16)
        for j in range(len(sections)):
            indexes[j] = np.abs(extracted_data[i][:, -1] - sections[j]).argmin()
        
        ## Compute metrics separately for each 60-second section
        for k in range(len(indexes) - 1):
            section = extracted_data[i][indexes[k]:indexes[k + 1]]
            if i == 0: 
                ## Step 1: Calculate expectation of mouse quadrant
                for m in range(quadrants.shape[0] - 1):
                    leftmask  = section[:, 0] >= quadrant_locs[m]
                    rightmask = section[:, 0] < quadrant_locs[m + 1]
                    quadrant_probs[k, m] = section[:, 0][leftmask & rightmask].shape[0]
                quadrant_probs[k] /= section[:, 0].shape[0]
                quadrant_expectation[k, i] = np.average(quadrants, weights = quadrant_probs[k])
                
                ## Step 2: Calculate Y axis standard deviation (SD)
                y_axis_sd[k, i] = np.std(section[:, 1])
            else:
                ## Step 3: Calculate mean step length
                steplength[k, i - 1] = np.mean(section[:, 2])
    
    ## Convert back into Pandas frame with row/column names for clarity
    row_names        = ['3m/min', '6m/min', '8m/min', '10m/min', '12m/min']
    quadrant_headers = ['E[Q]']
    head_headers     = ['HEAD']
    paw_headers      = ['LFP', 'RFP', 'LHP', 'RHP']
    quadrant_expectation_frame = pd.DataFrame(data = quadrant_expectation, index = row_names, columns = quadrant_headers)
    y_axis_sd_frame = pd.DataFrame(data = y_axis_sd, index = row_names, columns = head_headers)
    steplength_frame = pd.DataFrame(data = steplength, index = row_names, columns = paw_headers)

    ## Export frames to CSV
    fullname, ext = os.path.splitext(file)
    name = fullname.split('_')[0]
    quadrant_expectation_frame.to_csv(name + '_quadrant_expectation' + ext)
    y_axis_sd_frame.to_csv(name + '_y_axis_sd' + ext)
    steplength_frame.to_csv(name + '_steplength' + ext)

    ## Print metrics
    print("### Expectation of Mouse Quadrant ###")
    print(quadrant_expectation_frame)
    print("### Y Axis SD ###")
    print(y_axis_sd_frame)
    print("### Step Length ###")
    print(steplength_frame)

    ## Combine all metrics into one matrix
    allmetrics = np.hstack((quadrant_expectation, y_axis_sd, steplength))
    return allmetrics, box_coordinates

## Run metrics() function on CSV files in database
## Store in h5py file for use in mouse_coordination_score.py
## rerun_metrics: flag to indicate re-run metrics() function
##                on previously analyzed data
## rerun_box    : flag to indicate re-pick box corners from image 
def main(rerun_metrics = False, rerun_box = False):
    with ExitStack() as stack:
        ## Open h5py file to store all analyzed metrics
        mice_data    = stack.enter_context(h5py.File('mice_data.hdf5', 'a'))
        mice_metrics = stack.enter_context(h5py.File('mice_metrics.hdf5', 'a'))
        
        ## Create datasets for each metric separately
        ## Contains results from all mice for specific metric
        expectation    = None
        sd = None
        lfp_steplength = None
        rfp_steplength = None
        lhp_steplength = None
        rhp_steplength = None

        ## Load and delete existing metrics if needed
        if 'expectation' in mice_metrics:
            if not rerun_metrics:
                expectation    = mice_metrics['expectation'][...]
                sd = mice_metrics['sd'][...]
                lfp_steplength = mice_metrics['lfp_steplength'][...]
                rfp_steplength = mice_metrics['rfp_steplength'][...]
                lhp_steplength = mice_metrics['lhp_steplength'][...]
                rhp_steplength = mice_metrics['rhp_steplength'][...]

            del mice_metrics['expectation']
            del mice_metrics['sd']
            del mice_metrics['lfp_steplength']
            del mice_metrics['rfp_steplength']
            del mice_metrics['lhp_steplength']
            del mice_metrics['rhp_steplength']

        ## Compute mouse metrics for given mice
        ## Contains results of all metrics for a specific mouse on a specific day
        for mouse, days in database.items():
            for day, args in days.items():
                ## Create hdf5 keys
                data_key       = mouse + '/' + day + '/' + 'metrics'
                box_corner_key = mouse + '/' + day + '/' + 'box'
                ## Check if metrics for given mouse and day already exist before running metrics()
                if data_key not in mice_data or rerun_metrics:
                    file, raw_file, corners, reverse = args
                    ## Check if extracted box corners exist and pass to metrics()
                    if box_corner_key in mice_data and not rerun_box:
                        corners = mice_data[box_corner_key][...]
                    results, box_corners = metrics(file, raw_file, corners, reverse)
                    ## Store mouse's metrics in h5py file
                    if rerun_metrics and data_key in mice_data:
                        mice_data[data_key][...] = results
                    else:
                        mice_data.create_dataset(data_key, data = results)

                    ## Update each individual metric with mouse's results
                    if expectation is None:
                        expectation    = results[:, [0]]
                        sd = results[:, [1]]
                        lfp_steplength = results[:, [2]]
                        rfp_steplength = results[:, [3]]
                        lhp_steplength = results[:, [4]]
                        rhp_steplength = results[:, [5]]
                    else:
                        expectation    = np.hstack((expectation, results[:, [0]]))
                        sd = np.hstack((sd, results[:, [1]]))
                        lfp_steplength = np.hstack((lfp_steplength, results[:, [2]]))
                        rfp_steplength = np.hstack((rfp_steplength, results[:, [3]]))
                        lhp_steplength = np.hstack((lhp_steplength, results[:, [4]]))
                        rhp_steplength = np.hstack((rhp_steplength, results[:, [5]]))

                    ## Store box coordinates in h5py file
                    if rerun_box:
                        mice_data[box_corner_key][...] = box_corners
                    else:
                        if box_corner_key not in mice_data:
                            mice_data.create_dataset(box_corner_key, data = box_corners)
        
        ## Store individual metrics
        mice_metrics.create_dataset('expectation', data = expectation)
        mice_metrics.create_dataset('sd', data = sd)
        mice_metrics.create_dataset('lfp_steplength', data = lfp_steplength)
        mice_metrics.create_dataset('rfp_steplength', data = rhp_steplength)
        mice_metrics.create_dataset('lhp_steplength', data = lhp_steplength)
        mice_metrics.create_dataset('rhp_steplength', data = rhp_steplength)

main(rerun_metrics = True)
