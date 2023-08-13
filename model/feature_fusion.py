import torch
from torch import nn
from tool.config import Configuration


class FeatureFusion(nn.Module):
    def __init__(self, cfg: Configuration):
        super(FeatureFusion, self).__init__()
        self.cfg = cfg

        self.layer = nn.TransformerEncoderLayer(d_model=self.cfg.tf_en_dim, nhead=self.cfg.tf_en_heads)
        self.encoder = nn.TransformerEncoder(self.layer, num_layers=self.cfg.tf_en_layers)

        total_length = self.cfg.tf_en_bev_length
        self.pos_embedding = nn.Parameter(torch.randn(1, total_length, self.cfg.tf_en_dim) * .02)
        self.pos_dropout = nn.Dropout(self.cfg.tf_en_dropout)

        uint_dim = total_length / 4
        self.motion_encoder = nn.Sequential(
            nn.Linear(self.cfg.tf_en_motion_length, uint_dim),
            nn.ReLU(inplace=True),
            nn.Linear(uint_dim, uint_dim * 2),
            nn.ReLU(inplace=True),
            nn.Linear(uint_dim * 2, self.cfg.tf_en_dim),
            nn.ReLU(inplace=True),
        )

        self.init_weight()

    def init_weight(self):
        # Todo
        pass

    def forward(self, bev_feature, ego_motion):
        bev_feature = bev_feature.transpose(1, 2)
        motion_feature = self.motion_encoder(ego_motion).expand(-1, -1, 2)
        fuse_feature = torch.cat([bev_feature, motion_feature], dim=2)
        fuse_feature = self.pos_dropout(fuse_feature + self.pos_embedding)
        fuse_feature = fuse_feature.transpose(0, 1)
        fuse_feature = self.encoder(fuse_feature)
        fuse_feature = fuse_feature.transpose(0, 1)
        return fuse_feature
