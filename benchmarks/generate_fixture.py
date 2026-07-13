"""Generate the deterministic cross-software panel fixture."""

from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    entities, periods = 30, 8
    entity = np.repeat(np.arange(entities), periods)
    time = np.tile(np.arange(periods), entities)
    x = np.sin(entity * 0.7 + time * 0.4) + (entity % 4) * 0.1
    treated = (entity < 15).astype(int)
    post = (time >= 4).astype(int)
    noise = 0.08 * np.cos(entity * 1.3 + time * 0.9)
    y = (entity % 7) * 0.2 + time * 0.15 + 1.25 * x + 2.0 * treated * post + noise
    fixture = pd.DataFrame({"id": entity, "time": time, "x": x, "did": treated * post, "y": y})
    path = Path(__file__).with_name("panel_fixture.csv")
    fixture.to_csv(path, index=False, float_format="%.15g")


if __name__ == "__main__":
    main()
