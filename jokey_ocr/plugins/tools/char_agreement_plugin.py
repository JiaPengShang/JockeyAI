from typing import Optional, Any

from plugins.base import Plugin, PluginOutput, validate_plugin_output


class CharAgreementPlugin(Plugin):
    name = "char_agreement"
    version = "v1"

    def __init__(self, set_action: bool = False, t_review: float = 0.7, t_fix: float = 0.4):
        """
        When set_action=True , the action is automatically set/overwritten based on char_agreement:
- < t_fix -> "fix"
- < t_review -> "review"
- Otherwise, the original action remains.
        """
        self.set_action = set_action
        self.t_review = float(t_review)
        self.t_fix = float(t_fix)

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        a, b = a or "", b or ""
        la, lb = len(a), len(b)
        dp = list(range(lb + 1))
        for i in range(1, la + 1):
            prev, dp[0] = dp[0], i
            for j in range(1, lb + 1):
                cur = dp[j]
                cost = 0 if a[i - 1] == b[j - 1] else 1
                dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
                prev = cur
        return dp[lb]

    def _char_agreement(self, orig: str, corr: str) -> float:
        if not orig and not corr:
            return 1.0
        dist = self._levenshtein(orig or "", corr or "")
        denom = max(len(orig or ""), len(corr or ""), 1)
        return round(1.0 - dist / denom, 4)

    def process(
            self,
            image_path: str,
            upstream: Optional[PluginOutput] = None,
            **kwargs: Any,
    ) -> PluginOutput:
        out: PluginOutput = upstream or {"items": [], "meta": {}}
        items = out.get("items") or []
        print(f">>> running {self.name} plugin...")
        for it in items:
            orig = (it.get("orig") or "")
            corr = (it.get("corr") or orig)
            ca = self._char_agreement(orig, corr)
            it["char_agreement"] = ca

            if self.set_action:
                if ca < self.t_fix:
                    it["action"] = "fix"
                elif ca < self.t_review:
                    it["action"] = "review"
                else:
                    it.setdefault("action", "keep")

            validate_plugin_output(out, require_boxes=True)
            out.setdefault("meta", {})
            out["meta"]["stage"] = self.name
            out["meta"]["version"] = self.version
            return out