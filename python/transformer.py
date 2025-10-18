import torch
import torch.nn as nn

# ── model hyper-parameters ─────────────────────────────────────
MODEL_N_LANDMARKS = 478   # number of landmarks (sequence length)
MODEL_DMODEL      = 64    # embedding size
MODEL_NHEAD       = 4     # attention heads
MODEL_NLAYERS     = 3     # encoder layers
BEST_MODEL_PATH   = "./model/transformer.pth"

class SingleFramePositionalTransformer(nn.Module):
    """Predicts head Euler angles from one frame of facial landmarks."""

    def __init__(
        self,
        N: int      = MODEL_N_LANDMARKS,
        d_model: int = MODEL_DMODEL,
        nhead: int   = MODEL_NHEAD,
        nlayers: int = MODEL_NLAYERS,
        out_dim: int = 3,
    ):
        super().__init__()

        # embed (x, y) coordinates
        self.xy_embed   = nn.Linear(2, d_model)
        # landmark index embedding
        self.land_embed = nn.Embedding(N, d_model)

        # Transformer encoder
        enc_layer        = nn.TransformerEncoderLayer(d_model, nhead)
        self.transformer = nn.TransformerEncoder(enc_layer, nlayers)

        # regression head → Euler angles
        self.fc_out = nn.Linear(d_model, out_dim)

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """x: (B, N, 2), mask: (B, N) True = invalid"""
        seq = self.xy_embed(x) + self.land_embed(
            torch.arange(x.size(1), device=x.device)
        )
        seq = seq.permute(1, 0, 2)                   # to (N, B, d_model)
        enc = self.transformer(seq, src_key_padding_mask=mask)
        return self.fc_out(enc.mean(0))              # (B, 3)