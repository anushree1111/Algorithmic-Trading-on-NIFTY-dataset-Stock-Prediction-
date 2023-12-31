# -*- coding: utf-8 -*-
"""Algorithmic trading on NIFTY stock data .ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13TQoL59sPvQ6PnUlhFphiEs1fBsPY4Qx

**Dataset: [NIFTY-50 Stock Market Data (2000 - 2021)](https://www.kaggle.com/datasets/rohanrao/nifty50-stock-market-data?resource=download)**

The dataset is NIFTY-50 Stock Market Data from the years 2000-2021. NIFTY 50 is a benchmark Indian stock market index that represents the weighted average of 50 of the largest Indian companies listed on the National Stock Exchange (NSE). Each record in the dataset contains details about the stock's open, close, high, low prices, along with volume and other data for a particular day.

**Purpose:**
Our goal is to build a Deep Learning model to predict the closing price of the stocks of various companies listed in the NIFTY 50 index.

We use a simple Multi-Layer Perceptron (MLP) model, implemented in PyTorch, to achieve this.
"""

import zipfile

with zipfile.ZipFile('stockdata.zip', 'r') as zip_ref:
    zip_ref.extractall()

import os
files = os.listdir()
print(files)

"""**IMPORT LIBRARIES**"""

!pip install tensorflow

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

import tensorflow as tf
from tensorflow.python.keras.layers import Input, Dense
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
import matplotlib.pyplot as plt
import random

!pip install IPython

"""**LOAD DATA**"""

data = pd.read_csv('NIFTY50_all.csv')

"""StockDataset class allows us to convert our stock data (stored in arrays or lists) into tensor format, which is easy to use with PyTorch."""

import torch
from torch.utils.data import Dataset, DataLoader

class StockDataset(Dataset):
    def __init__(self, features, labels):
        self.features = features
        self.labels = labels

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return torch.tensor(self.features[idx], dtype=torch.float32), torch.tensor(self.labels[idx], dtype=torch.float32)

"""**FEED FORWARD NEURAL NETWORK, MLP**

It consists of a sequence of linear layers interspersed with *ReLU activation functions* and *dropout regularization*. The purpose of this MLP is to take the stock data's features and predict the next day's closing price, making it a *regression model*.

1. Rectified Linear Unit (ReLU) activation function. It returns the input if the input is greater than 0, otherwise it returns 0.

2. Dropout is a regularization technique. During training, it randomly sets a fraction of the input units to 0 at each update, which helps to prevent overfitting. Here, a dropout of 0.2 means 20% of the input units are set to 0. During evaluation, dropout is not applied.

**Overall Structure of the MLP:**

- The MLP has three fully connected layers (fc1, fc2, and fc3).
- Between the layers, ReLU activation is applied, except for the last layer.
- After the activations of the first and second layers, dropout regularization is applied.
- The final layer (fc3) has only 1 output neuron, which implies that our network predicts a single continuous value (regression).
"""

import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self, input_dim):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 1)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x

"""**PREPOCESSING AND TRAINING FUNCTION**

**Overview:**
**Data Processing:**

Extracts the data specific to the provided company.
Drops unnecessary columns to get features (X) and labels/target (y which is the 'VWAP' column).
Splits data into training, validation, and testing subsets.
Normalizes the data.


**Model Training:**

Loads the data into PyTorch DataLoaders for mini-batch processing.
Defines the model, loss function, and optimizer.
Trains the model for a specific number of epochs.

**Evaluation:**

Predicts the outputs for the training and testing sets.
Calculates the RMSE (Root Mean Square Error) for both sets.

**Visualization:**

Plays a sound (for a jupyter notebook environment) to alert that visualization is starting.
Plots the true vs predicted values for the testing set.
"""

from IPython.display import display, Audio
import numpy as np

def process_and_train(data, company_name, visualize=False):
    """
    Process the data for a given company, train a Deep Learning model on it,
    and possibly visualize the results.

    Args:
    - data: The entire dataframe.
    - company_name: The name of the company to process data for.
    - visualize: Whether to visualize the results or not.

    Returns:
    - train_rmse: The RMSE on the training data.
    - test_rmse: The RMSE on the testing data.
    """
    #Extract company-specific data based on the symbol column and make sure it matches
    company_data = data[data['Symbol'] == company_name]

    #feature selection: unecessary columns are dropped
    X = company_data.drop(columns=['Date', 'Symbol', 'Series', 'Prev Close', 'VWAP', 'Volume', 'Turnover', 'Trades', 'Deliverable Volume', '%Deliverble'])
    y = company_data['VWAP']

    #Split data into training, testing, and validation sets. The validation set is carved out of the training set.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.1, shuffle=False)

    #Normalization so that all the values are between 0 and 1. This helps the neural network converge faster.
    scaler_X = MinMaxScaler()
    X_train = scaler_X.fit_transform(X_train)
    X_val = scaler_X.transform(X_val)
    X_test = scaler_X.transform(X_test)

    scaler_y = MinMaxScaler()
    y_train = scaler_y.fit_transform(y_train.values.reshape(-1, 1))
    y_val = scaler_y.transform(y_val.values.reshape(-1, 1))
    y_test = scaler_y.transform(y_test.values.reshape(-1, 1))

    #The normalized data is converted to PyTorch datasets using the previously defined StockDataset class
    #and then loaded into data loaders for mini-batch processing.
    train_data = StockDataset(X_train, y_train)
    val_data = StockDataset(X_val, y_val)
    test_data = StockDataset(X_test, y_test)

    train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=64, shuffle=False)
    test_loader = DataLoader(test_data, batch_size=64, shuffle=False)

    #Model, Loss, Optimizer
    model = MLP(X_train.shape[1])
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    #Training loop:
    #For each epoch, it iterates over batches of data, computes the loss,
    #backpropagates the errors, and updates the model's weights.

    n_epochs = 50
    for epoch in range(n_epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    #Evaluation using Root Mean Square Error (RMSE), a common metric for regression problems.
    model.eval()
    with torch.no_grad():
        train_preds = model(torch.Tensor(X_train))
        test_preds = model(torch.Tensor(X_test))

        train_rmse = np.sqrt(mean_squared_error(y_train, train_preds.numpy()))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_preds.numpy()))

    #Visualization

    #If the visualize flag is set to True, a sound will be played, followed by a plot that compares
    #the model's predictions to the actual VWAP values for the test set. (optional)

    def play_sound():
      frq = 440  #Frequency set to 440Hz for the note 'A'
      dur = 1  #1 second
      t = np.linspace(0, dur, int(44100 * dur), endpoint=False)
      signal = np.sin(2 * np.pi * frq * t)
      return display.Audio(signal, rate=44100, autoplay=True)

    if visualize:
        play_sound()  #Play sound before visualization

        plt.figure(figsize=(14,6))
        plt.plot(scaler_y.inverse_transform(y_test), label="True", color="blue")
        plt.plot(scaler_y.inverse_transform(test_preds.numpy()), label="Predicted", color="red")
        plt.title(f"{company_name} - True vs Predicted VWAP")
        plt.legend()
        plt.grid(True)
        plt.show()

    return train_rmse, test_rmse

from IPython import display

#Processing and Training for each company in the dataset

companies = data['Symbol'].unique()
results = {}  #Storing the RMSE results for each company

#Visualizing for 5 random companies
np.random.seed(42)  #for reproducibility
visualize_companies = np.random.choice(companies, size=5, replace=False)

for company in companies:
    train_rmse, test_rmse = process_and_train(data, company, visualize=company in visualize_companies)
    results[company] = {'Train RMSE': train_rmse, 'Test RMSE': test_rmse}

#Displaying the results
results_df = pd.DataFrame(results).T
display.display(results_df)

#Summary statistics for train and test RMSE across all companies
print("\nSummary Statistics for RMSE:")
display.display(results_df.describe())

"""**RESULTS INTERPRETATION:**

The table presents the RMSE (Root Mean Square Error) for 65 companies, indicating the model's prediction accuracy for stock prices.

For each company (like MUNDRAPORT, ADANIPORTS, ASIANPAINT, etc.), there are two RMSE values:

**Train RMSE:** This indicates how well the model performed on the training dataset, i.e., the data that the model has seen and learned from.

**Test RMSE:** This indicates how well the model performed on unseen data, i.e., the data that the model did not use during the training process.

For example: for Asian Paints, the train RSME is **1.6439%** whereas the test RSME is **0.8522%**

**General Performance:** The model performs decently on training data, with average errors (RMSE) of **1.3233%**. However, on unseen data (test set), the error increases to **4.4675%** on average.

**Best vs. Worst:** The model's best performance on unseen data has an error of just **0.3342%**. In contrast, the worst performance shows a significantly high error of **39.5787%**.
"""