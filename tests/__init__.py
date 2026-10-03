from app import limiter

# Tests submit many times in a row; the rate limit is tested explicitly in test_submit
limiter.enabled = False
