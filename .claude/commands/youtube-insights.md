Analyse YouTube text signals from the local product-insights dumps.

First refresh/read the local data using the available MCP tool or `bash scripts/refresh-data.sh`.

Preferred MCP flow:
- call `run_daily_insights` for 30 days
- call `search_evidence` for `youtube`, `youtube_data_api`, `public_youtube_api`, `video_comment_thread`, `views_per_day`, `comments_per_day`, `Nubra API`, `Nubra trading app`, `option chain`, `broker API`, `websocket`, `strategy builder`, `payoff` and `algo trading`

Focus on comments, not thumbnails or video media.

Return:
1. Executive Summary
2. Retail YouTube Signals
   - Topic
   - User problem
   - Comment signal
   - Product implication
   - Nubra response
3. API/Algo YouTube Signals
   - Topic
   - Developer problem
   - Comment signal
   - Product implication
   - Nubra response
4. Videos/Channels Worth Tracking
   - Use views, comments, views/day, comments/day and engagement rate only to estimate reach and discussion intensity.
5. Competitor and Nubra Mentions
6. Content, Webinar and Lead-Magnet Ideas
7. Product Actions

Rules:
- Keep retail and API/algo separate.
- Treat comment pain points, questions and feature requests as the main insight source.
- Do not rank by views alone.
- Do not mention thumbnails.
- If no YouTube dump is available yet, clearly say the YouTube agent is ready but no YouTube data has been synced, then explain what data will appear after `YOUTUBE_API_KEY` is configured.
- Show the answer directly in chat. Do not create a PDF or Markdown file.
