"""
Capital allocation line (CAL) analysis: mixing a risky portfolio with a
risk-free asset.
"""


class CapitalAllocator:
    """
    Combines a risky portfolio with a risk-free asset to explore how
    different allocations affect overall expected return and risk.

    Parameters
    ----------
    portfolio : dict-like
        A dictionary or Series representing a single portfolio, containing
        at least 'Retorno Esperado' (expected return) and 'Risco' (risk/std).
    risk_free_rate : float
        Risk-free rate (e.g., monthly SELIC rate).

    Attributes
    ----------
    portfolio : dict
        The risky portfolio data.
    rf : float
        Risk-free rate.
    """

    def __init__(self, portfolio, risk_free_rate: float):
        self.portfolio = dict(portfolio)
        self.rf = risk_free_rate

    def weigh_risk_free(self, value: float, risk_free_value: float, p: float) -> float:
        """
        Combine a risky value with a risk-free value given proportion ``p``
        allocated to the risk-free asset.

        Parameters
        ----------
        value : float
            Value from the risky portfolio (e.g., expected return or risk).
        risk_free_value : float
            Corresponding value for the risk-free asset (0 for risk, rf for
            return).
        p : float
            Proportion allocated to the risk-free asset (0 to 1).

        Returns
        -------
        float
            Weighted value.
        """
        return p * risk_free_value + (1 - p) * value

    def capital_allocation_line(self, steps: int = 21) -> list[dict]:
        """
        Generate points along the Capital Allocation Line.

        Parameters
        ----------
        steps : int, optional
            Number of allocation points (default 21, i.e., 0% to 100% in 5%
            increments).

        Returns
        -------
        list of dict
            Each dict has keys 'p' (risk-free proportion), 'expected_return',
            'risk', and 'label'.
        """
        proportions = [i / (steps - 1) for i in range(steps)]
        points = []

        for p in proportions:
            expected_return = self.weigh_risk_free(
                self.portfolio["Retorno Esperado"], self.rf, p
            )
            risk = self.weigh_risk_free(self.portfolio["Risco"], 0.0, p)
            points.append(
                {
                    "p": p,
                    "expected_return": expected_return,
                    "risk": risk,
                    "label": f"{p:.0%} risk-free",
                }
            )

        return points

    def final_allocation(self, p: float) -> dict[str, float]:
        """
        Compute the final allocation weights given proportion ``p`` in the
        risk-free asset.

        Parameters
        ----------
        p : float
            Proportion allocated to the risk-free asset (0 to 1).

        Returns
        -------
        dict[str, float]
            Mapping of asset names (including 'Renda Fixa' for risk-free) to
            their allocation percentages.
        """
        allocation = {"Renda Fixa": p}
        for key, value in self.portfolio.items():
            if key not in ("Retorno Esperado", "Risco", "Sharpe"):
                allocation[key] = (1 - p) * value
        return allocation

    def expected_returns(self, p: float) -> tuple[float, float]:
        """
        Expected return and risk for a given allocation to the risk-free asset.

        Parameters
        ----------
        p : float
            Proportion allocated to risk-free (0 to 1).

        Returns
        -------
        tuple of (expected_return, risk)
        """
        ret = self.weigh_risk_free(self.portfolio["Retorno Esperado"], self.rf, p)
        ris = self.weigh_risk_free(self.portfolio["Risco"], 0.0, p)
        return ret, ris
