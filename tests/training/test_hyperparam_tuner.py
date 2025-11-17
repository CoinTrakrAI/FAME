from training.hyperparam import HyperparameterConfig, HyperparameterTuner


def objective(params):
    x = params["lr"]
    y = params["entropy"]
    return -(abs(x - 0.02) + abs(y - 0.01))


def test_hyperparameter_tuner_finds_good_params():
    config = HyperparameterConfig(
        search_space={
            "lr": [0.01, 0.02, 0.05],
            "entropy": [0.0, 0.01, 0.02],
        },
        max_trials=9,
        exploration_ratio=1.0,
        seed=42,
    )
    tuner = HyperparameterTuner(config, objective)
    results = tuner.run()
    assert any(
        res.params["lr"] == 0.02 and res.params["entropy"] == 0.01 and res.score >= -1e-6
        for res in results
    )

