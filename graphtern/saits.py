# Install PyPOTS first: pip install pypots==0.1.1
import numpy as np
from sklearn.preprocessing import StandardScaler
from pypots.data import load_specific_dataset, mcar, masked_fill
from pypots.imputation import SAITS
from pypots.utils.metrics import cal_mae
import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def create_saits_model(n_steps=8, n_features=4, n_layers=2, d_model=256, d_inner=128, n_heads=4, d_k=64, d_v=64, dropout=0.1, epochs=100):
    global saits
    saits = SAITS(n_steps=n_steps, n_features=n_features, n_layers=n_layers, d_model=d_model, d_inner=d_inner, n_heads=n_heads, d_k=d_k, d_v=d_v, dropout=dropout, epochs=epochs)
    return saits

def saits_model(X):
    global saits
    # Reshape the tensor to 2D (40 x 2)
    # tensor_2d = X.reshape(-1, 2).cpu().numpy()

    # # Create a StandardScaler object and fit it to the data
    # scaler = StandardScaler()
    # scaled_tensor_2d = scaler.fit_transform(tensor_2d)

    # # Reshape the scaled NumPy array back to the original shape (5 x 8 x 2)
    # X = torch.tensor(scaled_tensor_2d, dtype=torch.float32).view(*X.shape)

    # print(f'{saits.model.parameters()}')

    X_intact, X, missing_mask, indicating_mask = mcar(X, 0.1) # hold out 10% observed values as ground truth
    X = masked_fill(X, 1 - missing_mask, np.nan)
    dataset = {"X": X}
    saits.fit(dataset)  # train the model. Here I use the whole dataset as the training set, because ground truth is not visible to the model.
    imputation = saits.impute(dataset)
    imputation = torch.from_numpy(imputation)
    imputation = imputation.to(device)
    X_intact = X_intact.to(device)
    indicating_mask = indicating_mask.to(device)
    mae = cal_mae(imputation, X_intact, indicating_mask)
    return imputation, mae

def saits_impute(X):
    X_intact, X, missing_mask, indicating_mask = mcar(X, 0.1) # hold out 10% observed values as ground truth
    X = masked_fill(X, 1 - missing_mask, np.nan)
    dataset = {"X": X}
    imputation = saits.impute(dataset)
    imputation = torch.from_numpy(imputation)
    imputation = imputation.to(device)
    X_intact = X_intact.to(device)
    indicating_mask = indicating_mask.to(device)
    mae = cal_mae(imputation, X_intact, indicating_mask)
    return imputation, mae
