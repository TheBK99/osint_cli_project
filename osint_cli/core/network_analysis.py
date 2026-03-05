"""Propagation analysis using snscrape and NetworkX."""

from __future__ import annotations

import re

import networkx as nx

from osint_cli.models.investigation import NetworkAnalysisResult
from osint_cli.utils.logger import get_logger

logger = get_logger(__name__)


class NetworkAnalyzer:
    """Build a simple propagation graph from X posts."""

    def analyze_keyword(self, keyword: str, max_posts: int = 30) -> NetworkAnalysisResult:
        """Collect posts and compute centrality metrics."""
        posts = self._collect_posts(keyword, max_posts)
        graph = nx.DiGraph()

        earliest_poster: str | None = None
        earliest_ts = None

        for post in posts:
            user = post.get("user")
            if not user:
                continue
            graph.add_node(user)
            mentions = post.get("mentions", [])
            for mention in mentions:
                graph.add_edge(user, mention)

            ts = post.get("date")
            if ts and (earliest_ts is None or ts < earliest_ts):
                earliest_ts = ts
                earliest_poster = user

        centrality = nx.degree_centrality(graph) if graph.number_of_nodes() > 0 else {}
        top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

        return NetworkAnalysisResult(
            earliest_poster=earliest_poster,
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            top_degree_nodes=[(name, round(score, 4)) for name, score in top_nodes],
        )

    def _collect_posts(self, keyword: str, max_posts: int) -> list[dict[str, object]]:
        """Collect posts from snscrape in a resilient manner."""
        try:
            import snscrape.modules.twitter as sntwitter

            query = f"{keyword} lang:en"
            records: list[dict[str, object]] = []
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if i >= max_posts:
                    break
                mentions = re.findall(r"@([A-Za-z0-9_]{1,15})", tweet.rawContent)
                records.append(
                    {
                        "user": tweet.user.username,
                        "date": tweet.date,
                        "mentions": mentions,
                    }
                )
            return records
        except Exception as exc:
            logger.info("snscrape_failed", error=str(exc), keyword=keyword)
            return []
