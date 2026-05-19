import logging
from collections import Counter
from typing import Dict, Any, Optional
from django.db.models import Avg

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Builds and rebuilds the TherapeuticProfile for a user
    by aggregating all historical session feedback and mood data.
    The result is injected into the Claude prompt as "Returning User Context".
    """

    def rebuild_profile(self, user) -> 'TherapeuticProfile':
        """
        Full rebuild of the user's TherapeuticProfile from scratch.
        Called after every new SessionFeedback submission.
        """
        from apps.feedback.models import SessionFeedback, MoodEntry, TherapeuticProfile
        from apps.sessions.models import TherapySession

        profile, _ = TherapeuticProfile.objects.get_or_create(user=user)

        feedbacks = SessionFeedback.objects.filter(
            session__user=user
        ).select_related('session')

        # ── Technique effectiveness ───────────────────────────────────────
        technique_scores: Dict[str, list] = {}
        for fb in feedbacks:
            for technique in fb.techniques_resonated:
                technique_scores.setdefault(technique, []).append(fb.effectiveness_rating)
            for technique in fb.techniques_to_adjust:
                technique_scores.setdefault(technique, []).append(max(1, fb.effectiveness_rating - 2))

        # Sort by average score
        averaged = {
            t: sum(scores) / len(scores)
            for t, scores in technique_scores.items()
        }
        sorted_techniques = sorted(averaged.items(), key=lambda x: x[1], reverse=True)

        most_effective = [t for t, s in sorted_techniques if s >= 3.5][:5]
        least_effective = [t for t, s in sorted_techniques if s < 2.5][:5]

        # ── Mood improvement by category ──────────────────────────────────
        sessions_with_mood = (
            TherapySession.objects
            .filter(user=user, status='completed')
            .prefetch_related('mood_entries')
        )

        mood_by_category: Dict[str, list] = {}
        for session in sessions_with_mood:
            category = session.problem_category or 'general'
            for entry in session.mood_entries.filter(mood_after__isnull=False):
                delta = entry.mood_after - entry.mood_before
                mood_by_category.setdefault(category, []).append(delta)

        avg_mood_improvement = {
            cat: round(sum(deltas) / len(deltas), 2)
            for cat, deltas in mood_by_category.items()
        }

        # ── Key themes (from feedback notes) ─────────────────────────────
        all_notes = ' '.join(
            fb.general_notes for fb in feedbacks if fb.general_notes
        ).lower()
        # Simple theme extraction: most common meaningful words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'is', 'was', 'are', 'were', 'i', 'me', 'my', 'it', 'this', 'that',
                     'of', 'with', 'very', 'felt', 'feel', 'really', 'just', 'like', 'more'}
        words = [w.strip('.,!?()[]') for w in all_notes.split() if len(w) > 3 and w not in stopwords]
        word_counts = Counter(words)
        key_themes = [word for word, _ in word_counts.most_common(10)]

        # ── Update profile ────────────────────────────────────────────────
        profile.most_effective_techniques = most_effective
        profile.least_effective_techniques = least_effective
        profile.average_mood_improvement_by_category = avg_mood_improvement
        profile.session_count = TherapySession.objects.filter(
            user=user, status='completed'
        ).count()
        profile.key_themes = key_themes
        profile.save()

        logger.info(
            'Rebuilt therapeutic profile for user %s: %d sessions, top techniques: %s',
            user.id, profile.session_count, most_effective
        )
        return profile

    def build_therapeutic_profile(self, user) -> Optional[Dict[str, Any]]:
        """
        Return the profile as a dict for injection into the prompt template.
        Returns None if the user has no sessions yet (first-timer).
        """
        from apps.feedback.models import TherapeuticProfile

        try:
            profile = TherapeuticProfile.objects.get(user=user)
        except TherapeuticProfile.DoesNotExist:
            return None

        if profile.session_count == 0:
            return None

        return {
            'most_effective_techniques': profile.most_effective_techniques,
            'least_effective_techniques': profile.least_effective_techniques,
            'average_mood_improvement_by_category': profile.average_mood_improvement_by_category,
            'session_count': profile.session_count,
            'key_themes': profile.key_themes,
        }
