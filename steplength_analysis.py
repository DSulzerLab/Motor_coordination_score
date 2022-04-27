import pandas as pd
import statsmodels
import traja
from statsmodels import nonparametric
from statsmodels.nonparametric import smoothers_lowess
from pandas.core.window.rolling import Rolling

data = pd.read_csv("/path/to/input_file.csv")
data.columns = data.iloc[0,].str.cat(data.iloc[1,], sep="_")

## in raw data from DeepLabCut body parts are labeled with acronym: left front paw = lfp, right front paw = rfp, left hind paw = lhp, right hind paw = rhp

data = data.drop(['bodyparts_coords','head_likelihood','lfp_likelihood','lhp_likelihood','rfp_likelihood','rhp_likelihood','base_likelihood','tail_likelihood'], axis=1)

data = data[2:len(data)]
data = data.apply(pd.to_numeric)

data['time'] = pd.RangeIndex(0,(len(data)+2)).to_series()

traja_lfp = traja.TrajaDataFrame({"x": data['lfp_x'],"y": data['lfp_y'], "time": data['time']})
traja_rfp = traja.TrajaDataFrame({"x": data['rfp_x'],"y": data['rfp_y'], "time": data['time']})
traja_lhp = traja.TrajaDataFrame({"x": data['lhp_x'],"y": data['lhp_y'], "time": data['time']})
traja_rhp = traja.TrajaDataFrame({"x": data['rhp_x'],"y": data['rhp_y'], "time": data['time']})

data['lfp_steplength'] = traja.trajectory.step_lengths(traja_lfp)
data['rfp_steplength'] = traja.trajectory.step_lengths(traja_rfp)
data['lhp_steplength'] = traja.trajectory.step_lengths(traja_lhp)
data['rhp_steplength'] = traja.trajectory.step_lengths(traja_rhp)

data['lfp_steplength_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["lfp_steplength"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['rfp_steplength_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["rfp_steplength"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['lhp_steplength_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["lhp_steplength"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['rhp_steplength_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["rhp_steplength"],data["time"],frac=0.1, missing='drop', return_sorted=False))

data['lfp_steplength_roll_var'] = data['lfp_steplength'].rolling(50).var()
data['rfp_steplength_roll_var'] = data['rfp_steplength'].rolling(50).var()
data['lhp_steplength_roll_var'] = data['lhp_steplength'].rolling(50).var()
data['rhp_steplength_roll_var'] = data['rhp_steplength'].rolling(50).var()

data['lfp_steplength_roll_var_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["lfp_steplength_roll_var"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['rfp_steplength_roll_var_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["rfp_steplength_roll_var"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['lhp_steplength_roll_var_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["lhp_steplength_roll_var"],data["time"],frac=0.1, missing='drop', return_sorted=False))
data['rhp_steplength_roll_var_smooth'] = pd.DataFrame(statsmodels.nonparametric.smoothers_lowess.lowess(data["rhp_steplength_roll_var"],data["time"],frac=0.1, missing='drop', return_sorted=False))

data.to_csv(r'/path/to/output_file.csv')
