"""
Phase 1 — Data Extractor

Functions that extract structured data from a Playwright page object.
Each function corresponds to one section of the fund page.
Uses the page's tab navigation to access Overview, About, Holdings, and FAQs.
"""

from playwright.async_api import Page
from phase1.scraper.utils import clean_text, clean_percentage, parse_nav, logger


# ─── Tab Navigation ────────────────────────────────────────────────
async def click_tab(page: Page, tab_name: str) -> bool:
    """Click a tab button by its text content. Returns True if successful."""
    try:
        # IndMoney uses buttons inside ul.herolike-wrapper
        tabs = await page.query_selector_all("button")
        for tab in tabs:
            text = await tab.inner_text()
            if text and tab_name.lower() in text.strip().lower():
                await tab.click()
                await page.wait_for_timeout(1500)  # Wait for content to load
                return True
        logger.warning(f"Tab '{tab_name}' not found on page")
        return False
    except Exception as e:
        logger.warning(f"Failed to click tab '{tab_name}': {e}")
        return False


# ─── JSON-LD Extraction ────────────────────────────────────────────
async def extract_jsonld(page: Page) -> dict | None:
    """Extract structured data from script[type='application/ld+json']."""
    try:
        jsonld_data = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                const results = [];
                for (const s of scripts) {
                    try { results.push(JSON.parse(s.textContent)); }
                    catch(e) {}
                }
                return results;
            }
        """)
        if jsonld_data and len(jsonld_data) > 0:
            return jsonld_data[0] if isinstance(jsonld_data[0], dict) else None
    except Exception as e:
        logger.warning(f"JSON-LD extraction failed: {e}")
    return None


# ─── Overview Extraction ───────────────────────────────────────────
async def extract_overview(page: Page) -> dict:
    """Extract fund overview: name, NAV, date, category, benchmark."""
    result: dict = {
        "nav": None,
        "nav_date": None,
        "benchmark": None,
    }
    try:
        # Try JSON-LD first for NAV
        jsonld = await extract_jsonld(page)
        if jsonld:
            if "amount" in jsonld:
                result["nav"] = f"₹{jsonld['amount']}"

        # Get full page text-based data from Overview tab
        await click_tab(page, "Overview")

        # Direct NAV extraction from body text
        nav_text = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                // Match patterns like "NAV ₹19.18" or "NAV₹19.18" or "₹19.18"
                const match = body.match(/NAV[\\s]*₹\\s*([\\d,.]+)/);
                if (match) return '₹' + match[1];
                // Also try near top of page
                const match2 = body.match(/₹([\\d]+\\.\\d{2})/);
                return match2 ? '₹' + match2[1] : null;
            }
        """)
        if nav_text and not result["nav"]:
            result["nav"] = nav_text

        # Extract NAV date
        nav_date_text = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                const match = body.match(/NAV\\s*(?:as on|as of|on)[:\\s]*(\\d{1,2}\\s+\\w+\\s+\\d{4})/i);
                if (match) return match[1];
                const match2 = body.match(/(\\d{1,2}\\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\w*\\s+\\d{4})/i);
                return match2 ? match2[1] : null;
            }
        """)
        if nav_date_text:
            result["nav_date"] = clean_text(nav_date_text)

        # Get benchmark — look specifically for index names
        benchmark_text = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                // Match benchmark index names: "Nifty ...", "S&P BSE ...", "SENSEX ..."
                const match = body.match(/[Bb]enchmark[:\\s]*((?:Nifty|S\\&P BSE|SENSEX)[^\\n.]{5,80})/i);
                if (match) return match[1].trim();
                // Try finding "Nifty ... TR INR" or "Nifty ... TRI" pattern
                const match2 = body.match(/(Nifty\\s+(?:[A-Za-z\\s&]+?)\\s*(?:TR|TRI)\\s*(?:INR)?)/i);
                return match2 ? match2[1].trim() : null;
            }
        """)
        if benchmark_text:
            result["benchmark"] = clean_text(benchmark_text)

    except Exception as e:
        logger.error(f"Overview extraction failed: {e}")

    return result


# ─── Returns Extraction ────────────────────────────────────────────
async def extract_returns(page: Page) -> dict:
    """Extract fund returns for all time periods."""
    result: dict = {
        "1M": None, "3M": None, "6M": None,
        "1Y": None, "3Y": None, "5Y": None,
        "since_inception": None,
        "benchmark_returns": None,
    }
    try:
        # Click Performance tab if it exists, otherwise look in Overview
        await click_tab(page, "Performance")

        returns_data = await page.evaluate("""
            () => {
                const data = { fund: {}, benchmark: {} };
                // Look for table rows with return data
                const rows = document.querySelectorAll('tr');
                for (const row of rows) {
                    const cells = row.querySelectorAll('td, th');
                    if (cells.length >= 2) {
                        const label = cells[0].textContent.trim().toLowerCase();
                        if (label.includes('this fund') || label.includes('fund return')) {
                            const headers = row.closest('table')?.querySelectorAll('th');
                            if (headers) {
                                const periods = [];
                                for (const h of headers) {
                                    periods.push(h.textContent.trim());
                                }
                                for (let i = 1; i < cells.length && i < periods.length; i++) {
                                    data.fund[periods[i]] = cells[i].textContent.trim();
                                }
                            }
                        }
                        if (label.includes('benchmark') || label.includes('nifty')) {
                            const headers = row.closest('table')?.querySelectorAll('th');
                            if (headers) {
                                const periods = [];
                                for (const h of headers) {
                                    periods.push(h.textContent.trim());
                                }
                                for (let i = 1; i < cells.length && i < periods.length; i++) {
                                    data.benchmark[periods[i]] = cells[i].textContent.trim();
                                }
                            }
                        }
                    }
                }

                // Fallback: look for percentage values near period labels
                if (Object.keys(data.fund).length === 0) {
                    const body = document.body.textContent;
                    const patterns = [
                        { period: '1M', regex: /1\\s*[Mm]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                        { period: '3M', regex: /3\\s*[Mm]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                        { period: '6M', regex: /6\\s*[Mm]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                        { period: '1Y', regex: /1\\s*[Yy]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                        { period: '3Y', regex: /3\\s*[Yy]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                        { period: '5Y', regex: /5\\s*[Yy]\\w*[:\\s]*([-\\d.]+)\\s*%/ },
                    ];
                    for (const p of patterns) {
                        const match = body.match(p.regex);
                        if (match) data.fund[p.period] = match[1] + '%';
                    }
                }

                return data;
            }
        """)

        if returns_data:
            fund_returns = returns_data.get("fund", {})
            # Map period names from various formats
            period_map = {
                "1m": "1M", "1 m": "1M", "1 month": "1M",
                "3m": "3M", "3 m": "3M", "3 month": "3M", "3 months": "3M",
                "6m": "6M", "6 m": "6M", "6 month": "6M", "6 months": "6M",
                "1y": "1Y", "1 y": "1Y", "1 year": "1Y",
                "3y": "3Y", "3 y": "3Y", "3 year": "3Y", "3 years": "3Y",
                "5y": "5Y", "5 y": "5Y", "5 year": "5Y", "5 years": "5Y",
            }
            for key, val in fund_returns.items():
                normalized = key.lower().strip()
                if normalized in period_map:
                    result[period_map[normalized]] = clean_percentage(val) or val
                elif key in result:
                    result[key] = clean_percentage(val) or val

            benchmark_returns = returns_data.get("benchmark", {})
            if benchmark_returns:
                mapped_benchmark = {}
                for key, val in benchmark_returns.items():
                    normalized = key.lower().strip()
                    if normalized in period_map:
                        mapped_benchmark[period_map[normalized]] = clean_percentage(val) or val
                if mapped_benchmark:
                    result["benchmark_returns"] = mapped_benchmark

    except Exception as e:
        logger.error(f"Returns extraction failed: {e}")

    return result


# ─── Costs Extraction ──────────────────────────────────────────────
async def extract_costs(page: Page) -> dict:
    """Extract expense ratio, exit load, stamp duty."""
    result = {
        "expense_ratio": None,
        "exit_load": None,
        "stamp_duty": None,
        "transaction_charges": None,
    }
    try:
        await click_tab(page, "Overview")

        costs_data = await page.evaluate("""
            () => {
                const data = {};
                const body = document.body.textContent;

                // Expense ratio
                const erMatch = body.match(/[Ee]xpense\\s*[Rr]atio[:\\s]*(\\d+\\.?\\d*)\\s*%/);
                if (erMatch) data.expense_ratio = erMatch[1] + '%';

                // Exit load — look for percentage followed by redemption period
                const elMatch = body.match(/[Ee]xit\\s*[Ll]oad[^.]*?(\\d+\\.?\\d*)\\s*%\\s*(?:if|for|within|in)[^.]*?\\d+[^.]*(?:days?|months?|year)/i);
                if (elMatch) {
                    data.exit_load = elMatch[0].replace(/exit\\s*load\\s*/i, '').trim();
                } else {
                    // Fallback: just get the percentage
                    const elPctMatch = body.match(/[Ee]xit\\s*[Ll]oad[:\\s]*(\\d+\\.?\\d*)\\s*%/);
                    if (elPctMatch) data.exit_load = elPctMatch[1] + '%';
                }

                // Stamp duty
                const sdMatch = body.match(/[Ss]tamp\\s*[Dd]uty[:\\s]*(\\d+\\.?\\d*)\\s*%/);
                if (sdMatch) data.stamp_duty = sdMatch[1] + '%';

                return data;
            }
        """)

        if costs_data:
            result["expense_ratio"] = costs_data.get("expense_ratio")
            result["exit_load"] = costs_data.get("exit_load")
            result["stamp_duty"] = costs_data.get("stamp_duty")

        # Fallback: get exit load from FAQ answers
        if not result["exit_load"]:
            el_from_faq = await page.evaluate("""
                () => {
                    const body = document.body.textContent;
                    const match = body.match(/exit\\s*load\\s*is\\s*(\\d+\\.?\\d*%\\s*(?:if|for)[^.]+\\.)/i);
                    return match ? match[1].trim() : null;
                }
            """)
            if el_from_faq:
                result["exit_load"] = el_from_faq

    except Exception as e:
        logger.error(f"Costs extraction failed: {e}")

    return result


# ─── Risk Extraction ───────────────────────────────────────────────
async def extract_risk(page: Page) -> dict:
    """Extract riskometer, lock-in period, suitability."""
    result = {
        "riskometer": None,
        "risk_category": None,
        "lock_in_period": None,
        "suitable_for": None,
    }
    try:
        risk_data = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                const data = {};

                // Riskometer levels
                const riskLevels = [
                    'Very High', 'Very High Risk',
                    'High', 'High Risk',
                    'Moderately High', 'Moderate to High',
                    'Moderate', 'Moderate Risk',
                    'Low to Moderate',
                    'Low', 'Low Risk'
                ];
                for (const level of riskLevels) {
                    if (body.includes(level)) {
                        data.riskometer = level.replace(' Risk', '');
                        break;
                    }
                }

                // Lock-in period
                const lockMatch = body.match(/[Ll]ock[- ]?[Ii]n[:\\s]*([^\\.\\n]+)/);
                if (lockMatch) {
                    const val = lockMatch[1].trim();
                    data.lock_in = val.toLowerCase().includes('no') ? 'None' : val;
                }

                return data;
            }
        """)

        if risk_data:
            result["riskometer"] = risk_data.get("riskometer")
            result["lock_in_period"] = risk_data.get("lock_in", "None")

    except Exception as e:
        logger.error(f"Risk extraction failed: {e}")

    return result


# ─── Investment Details Extraction ─────────────────────────────────
async def extract_investment(page: Page) -> dict:
    """Extract minimum SIP, lumpsum, SIP frequency."""
    result: dict = {
        "minimum_sip": None,
        "minimum_lumpsum": None,
        "sip_frequency": None,
        "additional_purchase_min": None,
    }
    try:
        inv_data = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                const data = {};

                // Min SIP
                const sipMatch = body.match(/[Mm]in(?:imum)?\\s*SIP[:\\s]*₹?\\s*([\\d,]+)/);
                if (sipMatch) data.min_sip = '₹' + sipMatch[1];

                // Min Lumpsum
                const lsMatch = body.match(/[Mm]in(?:imum)?\\s*[Ll]umpsum[:\\s]*₹?\\s*([\\d,]+)/);
                if (lsMatch) data.min_lumpsum = '₹' + lsMatch[1];

                // Combined Min Lumpsum/SIP
                const combinedMatch = body.match(/[Mm]in\\s*[Ll]umpsum\\/SIP[:\\s]*₹?([\\d,]+)\\s*\\/\\s*₹?([\\d,]+)/);
                if (combinedMatch) {
                    data.min_lumpsum = '₹' + combinedMatch[1];
                    data.min_sip = '₹' + combinedMatch[2];
                }

                // If both are the same value pattern
                if (!data.min_sip && !data.min_lumpsum) {
                    const bothMatch = body.match(/₹(\\d+)\\s*\\/\\s*₹(\\d+)/);
                    if (bothMatch) {
                        data.min_lumpsum = '₹' + bothMatch[1];
                        data.min_sip = '₹' + bothMatch[2];
                    }
                }

                return data;
            }
        """)

        if inv_data:
            result["minimum_sip"] = inv_data.get("min_sip")
            result["minimum_lumpsum"] = inv_data.get("min_lumpsum")

    except Exception as e:
        logger.error(f"Investment extraction failed: {e}")

    return result


# ─── Portfolio / Holdings Extraction ───────────────────────────────
async def extract_portfolio(page: Page) -> dict:
    """Extract top holdings and sector allocation."""
    result: dict = {
        "top_holdings": [],
        "sector_allocation": None,
        "total_holdings": None,
        "portfolio_turnover": None,
    }
    try:
        await click_tab(page, "Holdings")
        await page.wait_for_timeout(2000)  # Wait for holdings to load

        holdings_data = await page.evaluate("""
            () => {
                const data = { holdings: [], sectors: {}, total: null };

                // Noise words to exclude from holdings names
                const noisePatterns = [
                    'NAV', 'This Fund', 'Sector -', 'Best in', 'Worst in',
                    'Equity', 'Debt', 'Large cap', 'Mid cap', 'Small cap',
                    'Debt & Cash', 'Cash', 'Others', 'cap', 'Cr',
                    'Nifty', 'SENSEX', 'benchmark', 'Average', 'Avg'
                ];

                // Try to find company names + percentages in Holdings tab
                const allText = document.body.innerText;
                const lines = allText.split('\\n').map(l => l.trim()).filter(l => l);

                // Track where "Holdings" section starts
                let inHoldingsSection = false;
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].toLowerCase().includes('top') &&
                        lines[i].toLowerCase().includes('holding')) {
                        inHoldingsSection = true;
                        continue;
                    }

                    if (!inHoldingsSection) continue;

                    // Stop if we hit another section
                    if (lines[i].toLowerCase().includes('sector allocation') ||
                        lines[i].toLowerCase().includes('asset allocation')) {
                        break;
                    }

                    // Pattern: "HDFC Bank Ltd" followed by "18.85%" on next line
                    const pctMatch = lines[i].match(/^([\\d.]+)\\s*%$/);
                    if (pctMatch && i > 0) {
                        const name = lines[i-1].trim();
                        // Filter out noise
                        const isNoise = noisePatterns.some(
                            p => name.toLowerCase().includes(p.toLowerCase())
                        );
                        if (name && name.length > 2 && name.length < 80 && !isNoise && !name.includes('%')) {
                            data.holdings.push({
                                name: name,
                                pct: pctMatch[1] + '%'
                            });
                        }
                    }

                    // Also try inline: "HDFC Bank Ltd  18.85%"
                    const inlineMatch = lines[i].match(/^(.+?)\\s+(\\d+\\.\\d+)\\s*%$/);
                    if (inlineMatch) {
                        const name = inlineMatch[1].trim();
                        const isNoise = noisePatterns.some(
                            p => name.toLowerCase().includes(p.toLowerCase())
                        );
                        if (!isNoise && name.length > 2 && name.length < 80) {
                            data.holdings.push({
                                name: name,
                                pct: inlineMatch[2] + '%'
                            });
                        }
                    }
                }

                // If no structured holdings found, try FAQ fallback
                if (data.holdings.length === 0) {
                    const body = document.body.textContent;
                    const hMatch = body.match(/top\\s*\\d+\\s*holdings.*?are\\s+(.+?)(?:\\.|$)/i);
                    if (hMatch) {
                        const pairs = hMatch[1].match(/([A-Za-z][A-Za-z &]+?)\\s*\\(?\\s*(\\d+\\.\\d+)\\s*%\\)?/g);
                        if (pairs) {
                            for (const pair of pairs) {
                                const m = pair.match(/(.+?)\\s*\\(?\\s*(\\d+\\.\\d+)\\s*%\\)?/);
                                if (m) {
                                    data.holdings.push({ name: m[1].trim(), pct: m[2] + '%' });
                                }
                            }
                        }
                    }
                }

                // Deduplicate
                const seen = new Set();
                data.holdings = data.holdings.filter(h => {
                    if (seen.has(h.name)) return false;
                    seen.add(h.name);
                    return true;
                });

                // Total holdings count
                const totalMatch = allText.match(/(\\d+)\\s*(?:stocks?|holdings?|companies)/i);
                if (totalMatch) data.total = parseInt(totalMatch[1]);

                return data;
            }
        """)


        if holdings_data:
            result["top_holdings"] = holdings_data.get("holdings", [])[:10]
            result["total_holdings"] = holdings_data.get("total")

    except Exception as e:
        logger.error(f"Portfolio extraction failed: {e}")

    return result


# ─── Fund Manager Extraction ──────────────────────────────────────
async def extract_manager(page: Page) -> dict:
    """Extract fund manager name and details."""
    result: dict = {
        "name": None,
        "experience": None,
        "qualification": None,
        "other_funds_managed": None,
    }
    try:
        await click_tab(page, "About")
        await page.wait_for_timeout(1500)

        manager_data = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                const data = {};

                // Fund manager name — usually near "Fund Manager" label
                const fmMatch = body.match(/[Ff]und\\s*[Mm]anager[:\\s]*([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)+)/);
                if (fmMatch) data.name = fmMatch[1].trim();

                // Also look for manager names in About section
                const aboutSection = document.body.innerText;
                const managerMatch = aboutSection.match(/(?:managed|manager)[:\\s]*(.+?)(?:\\.|\\n|since)/i);
                if (managerMatch && !data.name) {
                    data.name = managerMatch[1].trim();
                }

                return data;
            }
        """)

        if manager_data and manager_data.get("name"):
            result["name"] = clean_text(manager_data["name"])

    except Exception as e:
        logger.error(f"Manager extraction failed: {e}")

    return result


# ─── AUM Extraction ───────────────────────────────────────────────
async def extract_aum(page: Page) -> dict:
    """Extract Assets Under Management."""
    result: dict = {
        "value": None,
        "date": None,
        "trend": None,
    }
    try:
        aum_data = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                const data = {};

                // AUM value — look for pattern like "₹4486 Cr" or "₹4,486 Cr"
                const aumMatch = body.match(/AUM[:\\s]*₹?\\s*([\\d,]+\\.?\\d*)\\s*(?:Cr|Crore|cr)/i);
                if (aumMatch) data.value = '₹' + aumMatch[1] + ' Cr';

                // AUM date
                const dateMatch = body.match(/AUM\\s*(?:as on|as of)[:\\s]*(\\d{1,2}\\s+\\w+\\s+\\d{4})/i);
                if (dateMatch) data.date = dateMatch[1];

                return data;
            }
        """)

        if aum_data:
            result["value"] = aum_data.get("value")
            result["date"] = aum_data.get("date")

    except Exception as e:
        logger.error(f"AUM extraction failed: {e}")

    return result


# ─── FAQ Extraction ────────────────────────────────────────────────
async def extract_faqs(page: Page) -> list:
    """Extract FAQ Q&A pairs from the page."""
    faqs: list = []
    try:
        await click_tab(page, "FAQs")
        await page.wait_for_timeout(2000)

        faq_data = await page.evaluate("""
            () => {
                const faqs = [];
                // FAQ structure: h3 for questions, following elements for answers
                const headings = document.querySelectorAll('h3');
                for (const h of headings) {
                    const question = h.textContent.trim();
                    if (question && question.endsWith('?')) {
                        // Get the answer from the next sibling element(s)
                        let answer = '';
                        let next = h.nextElementSibling;
                        while (next && next.tagName !== 'H3') {
                            const text = next.textContent.trim();
                            if (text) answer += text + ' ';
                            next = next.nextElementSibling;
                        }
                        if (answer.trim()) {
                            faqs.push({
                                question: question,
                                answer: answer.trim()
                            });
                        }
                    }
                }

                // Fallback: look for summary/details (accordion pattern)
                if (faqs.length === 0) {
                    const details = document.querySelectorAll('details');
                    for (const d of details) {
                        const summary = d.querySelector('summary');
                        if (summary) {
                            const q = summary.textContent.trim();
                            const a = d.textContent.replace(q, '').trim();
                            if (q && a) faqs.push({ question: q, answer: a });
                        }
                    }
                }

                return faqs;
            }
        """)

        if faq_data:
            faqs = [
                {"question": clean_text(f["question"]), "answer": clean_text(f["answer"])}
                for f in faq_data
                if f.get("question") and f.get("answer")
            ]

    except Exception as e:
        logger.error(f"FAQ extraction failed: {e}")

    return faqs


# ─── Inception Date Extraction ────────────────────────────────────
async def extract_inception_date(page: Page) -> str | None:
    """Extract fund inception date."""
    try:
        date_text = await page.evaluate("""
            () => {
                const body = document.body.textContent;
                // Pattern: "Inception Date: 01-Jan-2013" or "started in July 2021"
                const match = body.match(/[Ii]nception\\s*(?:[Dd]ate)?[:\\s]*(\\d{1,2}[\\s/-]\\w+[\\s/-]\\d{4})/);
                if (match) return match[1];
                const match2 = body.match(/started\\s+(?:in|on)\\s+(\\w+\\s+\\d{4})/i);
                return match2 ? match2[1] : null;
            }
        """)
        return clean_text(date_text) if date_text else None
    except Exception as e:
        logger.warning(f"Inception date extraction failed: {e}")
        return None


# ─── Fund Name Extraction ─────────────────────────────────────────
async def extract_fund_name(page: Page) -> str | None:
    """Extract fund name from h1."""
    try:
        h1 = await page.query_selector("h1")
        if h1:
            text = await h1.inner_text()
            return clean_text(text)
    except Exception as e:
        logger.warning(f"Fund name extraction failed: {e}")
    return None
