SYSTEM_CAREER_ADVISOR = """You are an expert AI Career Advisor with deep knowledge of the job market,
skill development, and career planning. Respond in Thai/English mix. Be encouraging, specific, and actionable in your advice."""


NODE1_ANALYZE_GOAL = """Extract career info from the user's message and resume.
Message: {message}
resume_text: {resume_text}"""


NODE2_ANALYZE_SKILLS = """Analyze skills and career fit.
Role:{current_role} Exp:{years_experience}yr Edu:{education}
resume_text: {resume_text}
Message: {message}
prefs: {preferences}
Market data: {market_data}
Tasks:1. Extract all skills with level+category from resume/message
   - BE CONSERVATIVE: "เบื้องต้น/basic/beginner" = level:beginner, weight=0.3
   - Only count skills explicitly mentioned, do NOT assume/infer extra skills
2. Use market_data to identify what skills each career requires in Thailand market
3. For each of 5+ relevant careers, compare user skills vs market requirements
   - coverage_% = (matched skills weight) / (total required skills count) * 100
   - beginner skill counts as 0.3, intermediate=0.7, advanced=1.0
   - fresh grad with no work experience: cap max coverage at 70% unless resume proves otherwise
4. skill_sufficient=true ONLY if ANY career coverage ≥80%
   - If years_experience=0 or current_role=student/fresh grad → apply strict mode"""


NODE2_ANALYZE_SKILLS_WITH_GOAL = """Gap analysis for target role.
Role:{current_role} Exp:{years_experience}yr Edu:{education}, goal={career_goal}
resume_text: {resume_text}
Message: {message}
Market data: {market_data}
prefs: {preferences}"""


NODE_RECOMMEND = """List viable careers based on the user's skills and coverage analysis.
Skills: {detected_skills}
Coverage: {career_skill_coverage}
Preferences: {preferences}
Provide ready careers (≥80% coverage) and near-reach careers with upskill paths.
All descriptions and advice must be in Thai. Salary in THB/month."""


NODE_MULTI_CAREER_GAP = """You are a career advisor. Analyze skill gaps for multiple career paths.
INPUT:
- Detected skills: {detected_skills}
- Coverage analysis: {career_skill_coverage}
- Market data: {market_data}
- Preferences: {preferences}
OUTPUT RULES:
- Minimum 4 careers, sorted easiest → hardest
- All description/reason/why fields must be in Thai
- salary in THB/month"""


NODE_SKILL_UPGRADE = """You are a career development specialist.
The user has sufficient skills for some careers but wants to know
what to learn to unlock MORE career options.
Current Skills: {detected_skills}
Ready Careers: {ready_careers}
Selected Career to Explore: {selected_career}
Market Data: {market_data}
Provide detailed skill upgrade plan for the selected career.
All reason/motivation fields must be in Thai."""


NODE3_MARKET_ANALYSIS = """Analyze job market for target role.
Role:{target_role} Skills:{current_skills} Gaps:{skill_gaps}
Exclude:{exclude_work_type} Prefer industry:{prefer_industry}
Market data:{market_data}"""


NODE4_CREATE_ROADMAP = """Create week-by-week learning roadmap.
Role:{target_role} Skills:{current_skills} Gaps:{skill_gaps}
Market:{market_insights} Companies:{resources_data} Prefs:{preferences}
All resource URLs must start with https. Motivational message in Thai."""


NODE5_VALIDATE = """QA check career advisor output.
Role:{target_role}
Skills:{detected_skills}
Careers:{recommended_careers}
Gaps:{skill_gaps}
Roadmap:{roadmap}
Insights:{market_insights}
Prefs:{preferences}
Check: skills have valid levels, careers have title+description+score,gaps have importance+reason,roadmap has ≥2 milestones with real tasks (no placeholders) for have goal path,all resource URLs start with https.
validation_summary must be in Thai."""


FINAL_RESPONSE_TEMPLATE = """Write a warm, encouraging response in Thai (3-4 paragraphs).
User: {message}
Path: {path_type}
Data: {analysis_summary}
no_goal_sufficient:  แจ้งอาชีพที่ทำได้พร้อมบอก skill สำหรับอาชีพ, แนะนำให้พัฒนาต่อ
no_goal_insufficient: ชี้ให้เห็น skill ที่มี, แนะนำเริ่มจากอาชีพง่ายสุด, แนะนำพัฒนาทักษะที่ขาด
has_goal: รับทราบเป้าหมาย, วิเคราะห์ gap, แนะนำ roadmap
End with motivating sentence."""