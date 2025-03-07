from __future__ import division
import sys, os

#3os.environ["CUDA_VISIBLE_DEVICES"] = "3"
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import numpy as np
from sklearn.utils import shuffle
import re
import string
import math
from ROOT import TFile, TTree
from ROOT import *
import ROOT
import numpy as np
from keras import backend as K
from keras.models import Model, Sequential, load_model
from keras.layers import Input, Dense, Activation, Dropout, add, LSTM, Concatenate
from keras.regularizers import l2
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import Conv1D, Conv2D
from array import array
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from keras.utils.np_utils import to_categorical
from keras import optimizers
from keras.callbacks import Callback, ModelCheckpoint
from keras.layers.core import Reshape
import tensorflow as tf

resultTxt = "result_1206.txt"
resultDir = "/home/juhee5819/T2+/result/1206/2d_jetvar"
trainInput = "/home/juhee5819/T2+/array/ttbb_2018_4f_pt20_global.h5"
data = pd.read_hdf( trainInput)
data = data.drop(data[data['category']==6].index)

num_data = len( data )
# event variables
var_event = ['nbjets_m', 'ngoodjets', 'St', 'Ht']
# jet variables
var_jet = ["jet1_pt", "jet1_eta", "jet1_e", "jet1_m", "jet1_btag", "jet2_pt", "jet2_eta", "jet2_e", "jet2_m", "jet2_btag", "jet3_pt", "jet3_eta", "jet3_e", "jet3_m", "jet3_btag", "jet4_pt", "jet4_eta", "jet4_e", "jet4_m", "jet4_btag", "dR12", "dR13", "dR14", "dR23", "dR24", "dR34", "dRlep1", "dRlep2", "dRlep3", "dRlep4", "dRnu1", "dRnu2", "dRnu3", "dRnu4", "dRnulep1", "dRnulep2", "dRnulep3", "dRnulep4", "dRnulep12", "dRnulep13", "dRnulep14", "dRnulep23", "dRnulep24", "dRnulep34", "dEta12", "dEta13", "dEta14", "dEta23", "dEta24", "dEta34", "dPhi12", "dPhi13", "dPhi14", "dPhi23", "dPhi24", "dPhi34", "invm12", "invm13", "invm14", "invm23", "invm24", "invm34", "invmlep1", "invmlep2", "invmlep3", "invmlep4", "invmnu1", "invmnu2", "invmnu3", "invmnu4"]
#var_jet = ["jet1_pt", "jet1_eta", "jet1_e", "jet1_m", "jet1_btag", "jet1_CvsB", "jet1_CvsL", "dRlep1", "dRnu1", "dRnulep1", "jet2_pt", "jet2_eta", "jet2_e", "jet2_m", "jet2_btag", "jet2_CvsB", "jet2_CvsL", "dRlep2", "dRnu2", "dRnulep2", "jet3_pt", "jet3_eta", "jet3_e", "jet3_m", "jet3_btag", "jet3_CvsB", "jet3_CvsL", "dRlep3", "dRnu3", "dRnulep3", "jet4_pt", "jet4_eta", "jet4_e", "jet4_m", "jet4_btag", "jet4_CvsB", "jet4_CvsL", "dRlep4", "dRnu4", "dRnulep4"]

# lepton, MET variables
var_lepton = ["lepton_pt", "lepton_eta", "lepton_e", "MET", "MET_phi"]

# Split between training set and validation set
train_set = 0.7
for_valid = data[int( train_set * num_data ) : num_data]
for_train = data[0 : int( train_set * num_data )]

# inputs and outputs
train_data_out = for_train.filter( items = ['category'] )
train_event_input = for_train.filter( items = var_event )
train_jet_input = for_train.filter( items = var_jet )
train_lepton_input = for_train.filter( items = var_lepton )

valid_data_out = for_valid.filter( items = ['category'] )
valid_event_input = for_valid.filter( items = var_event )
valid_jet_input = for_valid.filter( items = var_jet )
valid_lepton_input = for_valid.filter( items = var_lepton )

catlist = valid_data_out.apply(set)
n_cat = catlist.str.len()
n_cat = int( n_cat )
print 'n_cat', n_cat
cat_num_list = [(len(for_train.loc[for_train['category'] == i])) for i in range(n_cat)]
print cat_num_list

# convert from pandas to array
train_data_out = np.array( train_data_out )
train_data_out = to_categorical( train_data_out )

train_event_input = np.array( train_event_input )
train_jet_input = np.array( train_jet_input )
train_lepton_input = np.array( train_lepton_input )

valid_data_out = np.array( valid_data_out )
valid_data_out = to_categorical( valid_data_out )

valid_event_input = np.array( valid_event_input )
valid_jet_input = np.array( valid_jet_input )
valid_lepton_input = np.array( valid_lepton_input )

# reshape array
train_data_out = train_data_out.reshape( train_data_out.shape[0], 1, train_data_out.shape[1] )
train_event_input = train_event_input.reshape( train_event_input.shape[0], 1, train_event_input.shape[1] )
train_jet_input = train_jet_input.reshape( train_jet_input.shape[0], 5, -1, 1 )
#train_jet_input = train_jet_input.reshape( train_jet_input.shape[0], 1, train_jet_input.shape[1] )
train_lepton_input = train_lepton_input.reshape( train_lepton_input.shape[0], 1, train_lepton_input.shape[1] )

valid_data_out = valid_data_out.reshape( valid_data_out.shape[0], 1, valid_data_out.shape[1] )
valid_event_input = valid_event_input.reshape( valid_event_input.shape[0], 1, valid_event_input.shape[1] )
valid_jet_input = valid_jet_input.reshape( valid_jet_input.shape[0], 5, -1, 1 )
#valid_jet_input = valid_jet_input.reshape( valid_jet_input.shape[0], 1, valid_jet_input.shape[1] )
valid_lepton_input = valid_lepton_input.reshape( valid_lepton_input.shape[0], 1, valid_lepton_input.shape[1] )

# Inputs
Input_event = Input( shape = (train_event_input.shape[1], train_event_input.shape[2]) )
Input_jet = Input( shape = (train_jet_input.shape[1], train_jet_input.shape[2], train_jet_input.shape[3]) )
Input_lepton = Input( shape = (train_lepton_input.shape[1], train_lepton_input.shape[2]) )

#Input_event = Input( shape = (train_event_input.shape[1], train_event_input.shape[2], 1) )
#Input_jet = Input( shape = (train_jet_input.shape[1], train_jet_input.shape[2], 1 ))
#Input_lepton = Input( shape = (train_lepton_inpuhape( valid_jet_input.shape[0],.shape[1], train_lepton_input.shape[2], 1 ))

# BatchNormalization
event_info = BatchNormalization( name = 'event_input_batchnorm' )(Input_event)
jets = BatchNormalization( name = 'jet_input_batchnorm' )(Input_jet)
leptons = BatchNormalization( name = 'lepton_input_batchnorm' )(Input_lepton)

# CNN for jets
jets = Conv2D(32, (2,2), padding='same', kernel_initializer='lecun_uniform',  activation='relu', name='jets_conv0')(jets)
jets = Conv2D(32, (2,2), padding='same',  kernel_initializer='lecun_uniform',  activation='relu', name='jets_conv1')(jets)
jets = Reshape( (1, -1) )(jets)
jets = LSTM(50, go_backwards=True, implementation=2, name='jets_lstm', return_sequences=True)(jets)
#jets = LSTM(50, go_backwards=True, implementation=2, name='jets_lstm2', return_sequences=True)(jets)

## CNN for leptons
#leptons  = Conv1D(32, 1, kernel_initializer='lecun_uniform',  activation='relu', name='leptons_conv0')(leptons)
#leptons = LSTM(25, go_backwards=True, implementation=2, name='leptons_lstm', return_sequences=True)(leptons)

nodes = 50
dropout = 0.08
# Concatenate
x = Concatenate()( [event_info, jets, leptons] )
x = Dense(nodes, activation='relu',kernel_initializer='lecun_uniform')(x)
x = Dropout(dropout)(x)

#n_cat = 6

cat_pred = Dense( n_cat, activation='softmax',kernel_initializer='lecun_uniform',name='cat_pred')(x)
model = Model( inputs = [Input_event, Input_jet, Input_lepton], outputs = cat_pred)

batch_size = 1024
epochs = 10

model.compile( loss = 'categorical_crossentropy',optimizer = 'adam',metrics=['accuracy', 'categorical_accuracy'] )
hist = model.fit( x = [train_event_input, train_jet_input, train_lepton_input], y = train_data_out, batch_size = batch_size, epochs = epochs, validation_data = ( [valid_event_input, valid_jet_input, valid_lepton_input], valid_data_out))

#pre = model.predict(valid_data)
pred = model.predict( [valid_event_input, valid_jet_input, valid_lepton_input])
pred = pred.reshape( pred.shape[0], pred.shape[2] )
pred = np.argmax(pred, axis=1)
valid_data_out_reshape = valid_data_out.reshape( valid_data_out.shape[0], valid_data_out.shape[2] )
comp = np.argmax(valid_data_out_reshape, axis=1)

val_result = pd.DataFrame({"real":comp, "pred":pred})#d event variables

result_array = []
correct = 0

for i in range(n_cat):
    result_real = val_result.loc[val_result['real']==i]
    temp = [(len(result_real.loc[result_real["pred"]==j])) for j in range(n_cat)]
    result_array.append(temp)
    correct = correct + temp[i]
    print temp, len(result_real), temp[i]

result_array_prob = []
for i in range(n_cat):
    result_real = val_result.loc[val_result['real']==i]
    temp = [(len(result_real.loc[result_real["pred"]==j])) / len(result_real) for j in range(n_cat)]
    result_array_prob.append(temp)
    print temp, len(result_real), temp[i]

print("Plotting scores")

recoeff = correct/(len(for_valid))*100
print 'recoeff', recoeff

with open(resultTxt, "a") as f_log:
    print 'writing results...'
    f_log.write("\ntrainInput "+trainInput+'\n')
    f_log.write('Nodes: '+str(nodes)+'\nEpochs '+str(epochs)+'\nDropout '+str(dropout)+'\n')
    f_log.write('nvar: '+str(var_event+var_jet+var_lepton)+'\n')
    f_log.write('reco eff: '+str(correct)+' / '+str(len(for_valid))+' = '+str(recoeff)+'\n')
    f_log.write('training samples '+str(len(for_train))+'   validation samples '+str(len(for_valid))+'\n')
    f_log.write('the number of each category '+str(cat_num_list)+'\n')
    f_log.write('reco eff: '+str(recoeff)+'\n')

# Loss
plt.plot(hist.history['loss'])
plt.plot(hist.history['val_loss'])
plt.ylabel('Loss')
plt.xlabel('Epochs')
plt.legend(['Train','Test'],loc='upper right')
plt.savefig(os.path.join(resultDir,'Loss_N'+str(nodes)+'E'+str(epochs)+'D'+str(dropout)+'.pdf'))
plt.gcf().clear()

# Heatmap
plt.rcParams['figure.figsize'] = [7.5, 6]
cfmt = lambda x,pos: '{:.0%}'.format(x)
heatmap = sns.heatmap(result_array_prob, annot=True, cmap='YlGnBu', fmt='.1%', annot_kws={"size":12}, vmax=1, cbar_kws={'format': FuncFormatter(cfmt)} )
#plt.title('Heatmap', fontsize=15)
plt.xlabel('pred.', fontsize=12)
plt.ylabel('real', fontsize=12)
heatmap.set_yticklabels(heatmap.get_yticklabels(), rotation=0)
plt.savefig(os.path.join(resultDir,'HM_N'+str(nodes)+'E'+str(epochs)+'D'+str(dropout)+'.pdf'))
plt.show()




