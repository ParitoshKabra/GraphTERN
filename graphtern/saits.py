# Install PyPOTS first: pip install pypots==0.1.1
import numpy as np
from sklearn.preprocessing import StandardScaler
from pypots.data import load_specific_dataset, mcar, masked_fill
from pypots.imputation import SAITS
from pypots.utils.metrics import cal_mae
import torch

def saits_model(X, n_steps=8, n_features=2, n_layers=2, d_model=256, d_inner=128, n_heads=4, d_k=64, d_v=64, dropout=0.1, epochs=10 ):
    # Reshape the tensor to 2D (40 x 2)
    tensor_2d = X.reshape(-1, 2).cpu().numpy()

    # Create a StandardScaler object and fit it to the data
    scaler = StandardScaler()
    scaled_tensor_2d = scaler.fit_transform(tensor_2d)

    # Reshape the scaled NumPy array back to the original shape (5 x 8 x 2)
    X = torch.tensor(scaled_tensor_2d, dtype=torch.float32).view(*X.shape)

    X_intact, X, missing_mask, indicating_mask = mcar(X, 0.1) # hold out 10% observed values as ground truth
    X = masked_fill(X, 1 - missing_mask, np.nan)
    saits = SAITS(n_steps=n_steps, n_features=n_features, n_layers=n_layers, d_model=d_model, d_inner=d_inner, n_heads=n_heads, d_k=d_k, d_v=d_v, dropout=dropout, epochs=epochs)
    dataset = {"X": X}
    saits.fit(dataset)  # train the model. Here I use the whole dataset as the training set, because ground truth is not visible to the model.
    imputation = saits.impute(dataset)
    imputation = torch.from_numpy(imputation)
    imputation = imputation.cuda()
    X_intact = X_intact.cuda()
    indicating_mask = indicating_mask.cuda()
    mae = cal_mae(imputation, X_intact, indicating_mask)
    return imputation, mae
