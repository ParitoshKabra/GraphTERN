import torch
import torch.nn as nn
import numpy as np


class BatchKMeans(nn.Module):
    def __init__(self, n_clusters, n_redo=1, max_iter=100, tol=1e-4, init_mode="kmeans++"):
        super(BatchKMeans, self).__init__()
        self.n_redo = n_redo
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.init_mode = init_mode
        self.register_buffer("centroids", None)

    def load_state_dict(self, state_dict, **kwargs):
        for k, v in state_dict.items():
            if "." not in k:
                assert hasattr(self, k), f"attribute {k} does not exist"
                delattr(self, k)
                self.register_buffer(k, v)

        for name, module in self.named_children():
            sd = {k.replace(name + ".", ""): v for k, v in state_dict.items() if k.startswith(name + ".")}
            module.load_state_dict(sd)

    @staticmethod
    def calculate_error(a, b):
        diff = a - b
        diff.pow_(2)
        return diff.sum()

    @staticmethod
    def calculate_inertia(a):
        return (-a).mean()

    @staticmethod
    def euc_sim(a, b):
        y = a.transpose(-2, -1) @ b
        y.mul_(2)
        y.sub_(a.pow(2).sum(dim=-2)[..., :, None])
        y.sub_(b.pow(2).sum(dim=-2)[..., None, :])
        return y

    def kmeanspp(self, data):
        d_vector, n_data = data.shape[-2:]
        centroids = torch.zeros(*data.shape[:-2], d_vector, self.n_clusters, device=data.device, dtype=data.dtype)
        # Select initial centroid
        centroids[..., 0] = data[..., np.random.randint(n_data)]
        for i in range(1, self.n_clusters):
            current_centroids = centroids[..., :i].contiguous()
            sims = self.euc_sim(data, current_centroids)  # [l,m,n]
            max_sims_v, max_sims_i = sims.max(dim=-1)  # [l,m]
            index = max_sims_v.argmin(dim=-1)  # [l]

            if len(data.shape) == 2:
                new_centroid = data[:, index]
            elif len(data.shape) == 3:
                arange = torch.arange(data.size(0), device=data.device)
                new_centroid = data[arange, :, index]  # [l, d_vector]
            elif len(data.shape) == 4:
                arange_w = torch.arange(data.size(0), device=data.device).unsqueeze(dim=1)
                arange_h = torch.arange(data.size(1), device=data.device).unsqueeze(dim=0)
                new_centroid = data[arange_w, arange_h, :, index]
            else:
                raise NotImplementedError

            centroids[..., i] = new_centroid
        return centroids

    def initialize_centroids(self, data):
        n_data = data.size(-1)
        if self.init_mode == "random":
            random_index = np.random.choice(n_data, size=[self.n_clusters], replace=False)
            centroids = data[:, :, random_index].clone()
        elif self.init_mode == "kmeans++":
            centroids = self.kmeanspp(data).clone()
        return centroids

    def get_labels(self, data, centroids):
        sims = self.euc_sim(data, centroids)  # [l, sub_m, n]
        maxsims, labels = sims.max(dim=-1)  # [l, sub_m]
        return maxsims, labels

    def compute_centroids_loop(self, data, labels):
        mask = [labels == i for i in range(self.n_clusters)]
        mask = torch.stack(mask, dim=-1)  # l d n_clusters
        centroids = (data.unsqueeze(dim=-1) * mask.unsqueeze(dim=-3)).sum(dim=-2) / mask.sum(dim=-2, keepdim=True)
        return centroids

    def compute_centroids(self, data, labels):
        centroids = self.compute_centroids_loop(data, labels)
        return centroids

    def fit(self, data, centroids=None):
        assert data.is_contiguous(), "use .contiguous()"

        best_centroids = None
        best_error = 1e32
        best_labels = None
        best_inertia = 1e32
        for i in range(self.n_redo):
            if centroids is None:
                centroids = self.initialize_centroids(data)
            for j in range(self.max_iter):
                # 1 iteration of clustering
                maxsims, labels = self.get_labels(data, centroids)  # top1 search
                new_centroids = self.compute_centroids(data, labels)
                error = self.calculate_error(centroids, new_centroids)
                centroids = new_centroids
                inertia = self.calculate_inertia(maxsims)
                if error <= self.tol:
                    break

            if inertia < best_inertia:
                best_centroids = centroids
                best_error = error
                best_labels = labels
                best_inertia = inertia
            centroids = None

        self.register_buffer("centroids", best_centroids)
        return best_labels

    def predict(self, query):
        _, labels = self.get_labels(query, self.centroids)
        return labels


if __name__ == "__main__":
    x = torch.randn(13, 29, 2, 1000).cuda()
    multi_k_means = BatchKMeans(n_clusters=20, n_redo=1)
    multi_k_means.fit(x)
    print(multi_k_means.centroids.shape)
