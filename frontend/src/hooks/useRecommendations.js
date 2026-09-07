import { useMemo } from "react";

export function selectRecommendations(
  recommendations,
  minMatch,
  onlyStrongSkills,
) {
  return recommendations
    .map((recommendation) => {
      const reasons = (recommendation.reasons ?? []).filter(
        (reason) => !reason.startsWith("score:"),
      );
      const semanticSignal = reasons.find((reason) =>
        reason.toLowerCase().includes("alta similitud"),
      )
        ? "alta"
        : reasons.find((reason) =>
              reason.toLowerCase().includes("buena alineación"),
            )
          ? "buenas"
          : "brechas";
      const categoryTag = reasons.find((reason) =>
        reason.startsWith("categoria:"),
      );
      const tagCategory = categoryTag ? categoryTag.split(":")[1] : null;
      const strongSkills =
        (
          reasons.find((reason) =>
            reason.toLowerCase().includes("skills fuertes"),
          ) ?? ""
        ).length > 0;
      return {
        ...recommendation,
        reasons: reasons.filter((reason) => !reason.startsWith("categoria:")),
        category: tagCategory ?? semanticSignal,
        strongSkills,
      };
    })
    .filter(
      (recommendation) =>
        recommendation.match_percentage >= 40 &&
        ((recommendation.skill_match_percentage ?? 0) >= 50 ||
          (recommendation.semantic_match_percentage ?? 0) >= 75 ||
          ((recommendation.skill_match_percentage ?? 0) >= 30 &&
            (recommendation.semantic_match_percentage ?? 0) >= 65)),
    )
    .filter((recommendation) =>
      onlyStrongSkills ? recommendation.strongSkills : true,
    )
    .filter((recommendation) =>
      minMatch ? recommendation.match_percentage >= minMatch : true,
    );
}

export function useRecommendations(
  recommendations,
  minMatch,
  onlyStrongSkills,
) {
  return useMemo(
    () => selectRecommendations(recommendations, minMatch, onlyStrongSkills),
    [recommendations, minMatch, onlyStrongSkills],
  );
}
