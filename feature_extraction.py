# -*- coding: utf-8 -*-
"""Feature_Extraction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oejQk4w4BZ3HOBcISUiePtvDIpSkymFk

# Imports
"""

from moabb.datasets import BNCI2014001
from moabb.paradigms import (LeftRightImagery, MotorImagery,
                             FilterBankMotorImagery)

import os

#!pip install numpy --upgrade
import numpy as np


from tqdm import tqdm

from scipy.signal import welch, spectrogram
from scipy.ndimage.interpolation import shift
from scipy.stats import kurtosis, skew

"""# Feature Extraction

### Window Funciton
"""

def next_pos(data, window_size, overlap_size, seq_axis):
  sample_length = data.shape[seq_axis]
  pos = 0
  while (data.shape[seq_axis] > pos+window_size):
    yield pos 
    pos += window_size - overlap_size

def overlap_window(data, window_size, overlap_size, seq_axis):
  '''
  Takes data and creates overlapping windows. 

  Args:
      data:         Data in format: trial x channel x sequence
      window_size:  The size of the window in samples
      overlap_size: number of samples of overlap of current window with previous window
      seq_axis:     The axis the windowing is calculated on.

  Returns:
      The windowed data in format: trial x channel x windows x window_size
  '''

  sidx = []
  for i in next_pos(data, window_size, overlap_size, seq_axis):
    sidx.append(i)
  windows = []
  for i in sidx:#[1:]:
    windows.append(data[...,i:i+window_size, np.newaxis])
  
  windows= np.concatenate(windows, axis=-1)

  return np.swapaxes(windows, -1, -2) # trial x channel x window x sample

"""## Features"""

def normalize_axis(data, ax) :
    mean = np.mean(data, axis=ax)
    float_data = data.astype(np.float64)
    mean_centered = float_data - mean[...,np.newaxis]
    std = np.std(mean_centered, axis=ax)
    normalized = mean_centered/std[...,np.newaxis]
    return normalized

"""### Power Spectral Density"""

def psd_feature(windowed_data, normalize=False, sample_freq=250, cutoff_freq=60): #use 250Hz, 

  f, psd = welch(windowed_data, sample_freq, nperseg=windowed_data.shape[3], axis=-1) #use the full window size for nperseg

  idx = np.argwhere(f<cutoff_freq) 
  psd = psd[..., idx]               #select freq_bins less then cut off
  psd = np.swapaxes(np.squeeze(psd), -1, -2) #put window as last dim

  if normalize:
    psd = normalize(psd, 3)
  

  return  psd# returns trial x channel x freq_bin x window

#huh = psd_feature(Z)
#print(huh.shape)
#print(huh[0,0,0,:])

"""### Zero Crossings

"""

def zero_crossings(windowed_data, normalize=False):
  shifted = np.roll(windowed_data, 1, axis=3)
  signs = windowed_data[...,1:] * shifted[...,1:] <=0
  crossings = np.sum(signs, axis=3)
  crossings = np.squeeze(crossings)
  
  if normalize:
    crossings = normalize_axis(crossings, 2)
  
  return crossings

#crossings = zero_crossings(Z, True)
#print(crossings.shape)
#print(crossings[0,1,:])

"""### Kurtosis"""

def window_kurtosis(data, normalize = False):
  k = kurtosis(data, axis=3)

  if normalize:
    k = normalize_axis(k,2)
  
  return k

#k = window_kurtosis(Z, True)
#print(k.shape)
#print(k[0,0,:])

"""### Abs under curve"""

def abs_under_curve(windowed_data):
  abs_data = np.abs(windowed_data)
  return np.sum(abs_data, axis=3)

#absdata = abs_under_curve(Z)
#print(absdata.shape)
#Eprint(absdata[0,0,:])

"""### Skewedness"""

#skewedness = skew(Z, axis=3)
#print(skewedness.shape)
#print(skewedness[0,0,:])

"""### Peak-Peak"""

def pkpk(windowed_data):
  pk = np.max(windowed_data, axis=3) - np.min(windowed_data, axis=3)
  return pk

#p = pkpk(Z)
#print(p.shape)
#print(p[0,0,:])

"""## Extract Freatures"""

def extract_features(windowed_data):
  '''
  Takes windowed time series data and computes freqency and statistical features for each window. 
  
  Features computed are (25 total): power spectral density for 18 different frequecies, kurtosis, 
  abosulute area under curve, zero crossings, mean, varience, skewedness, and peak to peak
  
  Args:
      windowed_data:    Data in format: trials x channels x windows x window_size
  
  Returns:
      The windowed data in format: trials x channels x features x windows
  '''

  psd = psd_feature(windowed_data)
  k = window_kurtosis(windowed_data)
  abs_under = abs_under_curve(windowed_data)
  zeros = zero_crossings(windowed_data)
  mean = np.mean(windowed_data, axis=3)
  var = np.var(windowed_data, axis=3)
  skewedness = skew(windowed_data, axis=3)
  pk = pkpk(windowed_data)

  #Since these are only 1 feature the features axis needs to be created
  k = k[:,:,np.newaxis,:]                     
  abs_under = abs_under[:,:,np.newaxis,:]
  zeros = zeros[:,:,np.newaxis,:]
  mean = mean[:,:,np.newaxis,:]
  var = var[:,:,np.newaxis,:]
  skewedness = skewedness[:,:,np.newaxis,:]
  pk = pk[:,:,np.newaxis,:]

  features = np.concatenate((psd,k), axis=2)
  features = np.concatenate((features, abs_under), axis=2)
  features = np.concatenate((features, zeros), axis=2)
  features = np.concatenate((features, mean), axis=2)
  features = np.concatenate((features, var), axis=2)
  features = np.concatenate((features, skewedness), axis=2)
  features = np.concatenate((features, pk), axis=2)

  return features

"""# Main"""

def main():
  dataset = BNCI2014001()
  paradigm = MotorImagery(n_classes=4)
  X, y, metadata = paradigm.get_data(dataset=dataset)

  Z = overlap_window(X, 75, 37, 2) # trial x channel x window x sample
  print("windowed data shape: ", Z.shape)

  all_features = extract_features(Z) #final shape trials x Channels x Feature x Window
  print(all_features.shape)

if __name__ == "__main__":
  main()