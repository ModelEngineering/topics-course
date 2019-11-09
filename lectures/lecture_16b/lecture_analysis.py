"""Analysis Codes for Lecture"""

import numpy as np
import model_fitting as mf
import tellurium as te
import matplotlib.pyplot as plt
import pandas as pd
import lmfit
import os
import re

# Symbols
# Column names
TIME = 'time'

TIME_TO_POINT = 10 # 1 point for every second
NUM_POINTS = 120
START_TIME = 0
END_TIME = 1200


################### Functions ####################
def cleanColumns(df_data, is_force_time=False):
  """
  Cleans the column names in the dataframe,
  removing "[", "]". Makes time index.
  :param pd.DataFrame df_data: Simulation data output.
  :param bool is_force_time: force time to factors of 10
  """
  df = df_data.copy()
  columns = []
  for col in df_data.columns:
    new_col = str(col)
    new_col = new_col.replace("[", "")
    new_col = new_col.replace("]", "")
    columns.append(new_col)
  df.columns = columns
  if TIME in df.columns:
    df = df.set_index(TIME)
    if is_force_time:
      times = [float(TIME_TO_POINT*(t//TIME_TO_POINT)) for t in df.index]
      df.index = times
  return df

def simulate(model, start_time=START_TIME, end_time=END_TIME, num_points=NUM_POINTS,
    is_mrna=True, is_protein=True, is_input=False):
  """
  Runs a simulation for the modeling game. Allows for selection
  of the desired outputs.
  :param str model:
  :param bool is_mrna: include mRNA in output
  :param bool is_protein: include proteins in output
  :param bool is_input: include input in output
  :return pd.DataFrame: Dataframe with time as index
  """
  def delColumn(df, string):
    for col in df.columns:
      if col[:len(string)] == string:
        del df[col]
  #
  rr = te.loada(model)
  data = rr.simulate(start_time, end_time, num_points)
  df = pd.DataFrame(data)
  df.columns = data.colnames
  df = cleanColumns(df, is_force_time=True)
  #
  if not is_mrna:
    delColumn(df, "mRNA")
  if not is_protein:
    delColumn(df, "P")
  if not is_input:
    delColumn(df, "INPUT")
  return df

def getRNASeq(csv_file):
  """
  Get RNA sequence data from a local csv file.
  :param str csv_file:
  :return pd.DataFrame: cleans column names; time is index.
  """
  path = os.path.join("data", csv_file)
  df = pd.read_csv(path)
  df[TIME] = [int(v) for v in df[TIME]]
  df = df.set_index(TIME)
  return df

def makeResiduals(model, df, **kwargs):
  """
  Calculates the residuals for the columns in common.
  :param str model:
  :param pd.DataFrame df: observational data compatible with
                          model simulation.
  :param dict kwargs: optional parameters for simulation
  """
  df_sim = simulate(model, **kwargs)
  columns = set(df_sim.columns).intersection(df.columns)
  return df[columns] - df_sim[columns]

def plotData(df_data, starttime=0, endtime=1200):
  last = int(endtime/TIME_TO_POINT)
  indices = list(range(last))
  plt.plot(df_data.index[0:last], df_data.loc[df_data.index[indices],:])
  plt.xlabel("Time")
  plt.legend(df_data.columns, loc="upper right")

def makeParameters(constants):
  """
  Creates parameters with the correct ranges based on their names.
  :param str constants: names of constant
  """
  if isinstance(constants, str):
      constants = [constants]
  # mins and maxs for parameters by their initial string (up to a number)
  ranges_dict = {"Vm": (0.5, 2), "K": (0.01, 0.03), "H": (2, 8), 
                 "d_protein": (0.01, 0.03), "d_mRNA": (0.5, 2) }
  parameters = lmfit.Parameters()
  for constant in constants:
    pfxs = re.findall(r"^\D+", constant)
    if len(pfxs) != 1:
        raise ValueError("Cannot find match for %s" % constant)
    pfx = pfxs[0]
    min_val, max_val = ranges_dict[pfx]
    initial_val = (min_val + max_val) / 2
    parameters.add(constant, value=initial_val, min=min_val, max=max_val)
  return parameters