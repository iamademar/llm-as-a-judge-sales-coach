"""
Seed script to create three organizations with varied SPIN performance profiles.

Creates:
- 3 organizations (TechFlow Solutions, MidMarket Dynamics, StartupGrow Inc)
- 8 representatives per organization (24 total)
- ~25 conversations per rep per month for 3 months (Oct-Dec 2025)
- Assessments with realistic score distributions and trending
- 1 user per organization for login access

Usage:
    docker compose exec fastapi python -m scripts.seed

Options:
    --clear: Clear existing data before seeding
"""
import sys
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.crud import user as user_crud
from app.crud import representative as rep_crud
from app.crud import prompt_template as template_crud
from app.models.organization import Organization
from app.models.representative import Representative
from app.models.transcript import Transcript
from app.models.assessment import Assessment


# ===== Configuration =====

# Organization profiles with performance characteristics
ORG_PROFILES = {
    "TechFlow Solutions": {
        "description": "High-performing enterprise sales organization",
        "composite_range": (4.0, 4.8),
        "dimension_ranges": {
            "situation": (4.0, 5.0),
            "problem": (4.0, 5.0),
            "implication": (3.5, 4.5),  # Weaker dimension
            "need_payoff": (4.0, 5.0),
            "flow": (4.0, 5.0),
            "tone": (4.0, 5.0),
            "engagement": (4.0, 5.0),
        },
        "trend": "improving",  # Scores improve over time
        "std_dev": 0.3,
        "user_email": "admin@techflow.com",
    },
    "MidMarket Dynamics": {
        "description": "Moderate performing mid-market sales team",
        "composite_range": (3.0, 3.8),
        "dimension_ranges": {
            "situation": (3.0, 4.0),
            "problem": (3.0, 4.0),
            "implication": (3.0, 4.0),
            "need_payoff": (2.5, 3.5),  # Weaker dimension
            "flow": (3.0, 4.0),
            "tone": (3.0, 4.0),
            "engagement": (3.0, 4.0),
        },
        "trend": "stable",  # Scores remain consistent
        "std_dev": 0.4,
        "user_email": "admin@midmarket.com",
    },
    "StartupGrow Inc": {
        "description": "Early-stage sales team with development needs",
        "composite_range": (2.0, 3.2),
        "dimension_ranges": {
            "situation": (2.5, 3.5),
            "problem": (2.5, 3.5),
            "implication": (1.5, 2.5),  # Weak dimension
            "need_payoff": (1.5, 2.5),  # Weak dimension
            "flow": (2.0, 3.0),
            "tone": (2.5, 3.5),
            "engagement": (2.0, 3.0),
        },
        "trend": "improving",  # Scores improve slowly over time
        "std_dev": 0.5,
        "user_email": "admin@startupgrow.com",
    },
}

# Representative names and departments
REP_NAMES = {
    "TechFlow Solutions": [
        ("Alice Thompson", "Enterprise Sales", "alice.thompson@techflow.com"),
        ("Robert Kim", "Enterprise Sales", "robert.kim@techflow.com"),
        ("Jennifer Martinez", "Strategic Accounts", "jennifer.martinez@techflow.com"),
        ("William Chen", "Enterprise Sales", "william.chen@techflow.com"),
        ("Patricia Anderson", "Strategic Accounts", "patricia.anderson@techflow.com"),
        ("James Wilson", "Enterprise Sales", "james.wilson@techflow.com"),
        ("Linda Davis", "Strategic Accounts", "linda.davis@techflow.com"),
        ("Michael Brown", "Enterprise Sales", "michael.brown@techflow.com"),
    ],
    "MidMarket Dynamics": [
        ("Sarah Johnson", "Mid-Market Sales", "sarah.johnson@midmarket.com"),
        ("David Lee", "SMB Sales", "david.lee@midmarket.com"),
        ("Jessica Garcia", "Mid-Market Sales", "jessica.garcia@midmarket.com"),
        ("Christopher Taylor", "SMB Sales", "christopher.taylor@midmarket.com"),
        ("Amanda White", "Mid-Market Sales", "amanda.white@midmarket.com"),
        ("Daniel Moore", "SMB Sales", "daniel.moore@midmarket.com"),
        ("Michelle Rodriguez", "Mid-Market Sales", "michelle.rodriguez@midmarket.com"),
        ("Kevin Jackson", "SMB Sales", "kevin.jackson@midmarket.com"),
    ],
    "StartupGrow Inc": [
        ("Emily Parker", "Sales", "emily.parker@startupgrow.com"),
        ("Brian Foster", "Sales", "brian.foster@startupgrow.com"),
        ("Rachel Green", "Sales", "rachel.green@startupgrow.com"),
        ("Justin Harris", "Sales", "justin.harris@startupgrow.com"),
        ("Nicole Martinez", "Sales", "nicole.martinez@startupgrow.com"),
        ("Andrew Scott", "Sales", "andrew.scott@startupgrow.com"),
        ("Stephanie Turner", "Sales", "stephanie.turner@startupgrow.com"),
        ("Brandon Lewis", "Sales", "brandon.lewis@startupgrow.com"),
    ],
}

# Transcript templates by performance level
TRANSCRIPT_TEMPLATES = {
    "high": [
        """Rep: Hi {buyer_name}, thanks for taking the time today. I understand you're the {buyer_title} at {buyer_company}. How's your day going so far?

Buyer: Good, thanks. Pretty busy but I'm interested to learn more about your solution.

Rep: Absolutely, I appreciate you making the time. Before I dive in, I'd love to understand a bit more about your current setup. Can you walk me through how your team handles {process} today?

Buyer: Sure. Right now we're using {current_tool}, but honestly it's becoming a bottleneck. We have about {team_size} people touching it daily.

Rep: Got it. So with {team_size} daily users on {current_tool}, where are you seeing the biggest friction points? What's taking up the most time or causing the most headaches?

Buyer: The main issue is {pain_point}. It's costing us probably {time_impact} hours per week across the team.

Rep: {time_impact} hours weekly - that's significant. If we think about that compounding over quarters, what impact is that having on your ability to {business_goal}?

Buyer: Yeah, that's exactly the problem. We've missed {missed_target} already this quarter because of these delays. It's affecting our {business_metric}.

Rep: Missing {missed_target} has real consequences. If you could eliminate that bottleneck completely, what would that enable your team to do differently? What opportunities could you pursue that you can't today?

Buyer: Well, we could finally {opportunity_1} and probably {opportunity_2}. That's honestly what I'm most excited about.

Rep: That makes total sense. Let me show you how teams in similar situations have used our platform to achieve exactly that...""",

        """Rep: Hi {buyer_name}, great to connect. I know you're coming from the {industry} space. How are things going in your world right now?

Buyer: Busy as usual. We're in a growth phase which is exciting but also challenging.

Rep: Growth phases definitely bring unique challenges. What does your current {process} workflow look like as you're scaling?

Buyer: We've been cobbling together {tool_1} and {tool_2}, but it's not really designed for the volume we're at now.

Rep: I see. At what point did you start noticing those tools weren't keeping up? What specifically started breaking down?

Buyer: Around {threshold} per month, we started seeing {issue_1} and {issue_2}. Our team is spending way too much time on manual workarounds.

Rep: Manual workarounds at that scale - that has to be impacting your team's bandwidth. What are the downstream effects on your {department} team's ability to deliver?

Buyer: It's hitting us hard. We've had to delay {project} and our {metric} has dropped {percentage}. Management is asking questions.

Rep: If this continues on the current trajectory, what does the next quarter look like for your team's goals? What's at stake?

Buyer: Honestly, we risk losing {customer_segment} if we can't turn this around. That's a {revenue_impact} revenue impact potentially.

Rep: That's a critical situation. If you had a solution that could handle your current volume plus growth, what would success look like for you in 90 days?

Buyer: We'd need to get back to {target_metric} and be able to launch {strategic_initiative}. That's non-negotiable at this point.

Rep: Perfect. Let me show you how we've helped companies in similar situations...""",
    ],

    "medium": [
        """Rep: Hi {buyer_name}, thanks for joining. I'm calling from {rep_company}. Do you have a few minutes?

Buyer: Sure, I have about 20 minutes.

Rep: Great. I wanted to talk to you about {product_category}. Are you currently using anything for that?

Buyer: Yes, we're using {current_tool} right now.

Rep: Okay. How's that working out for you?

Buyer: It's okay, but we have some issues with {pain_point}. It's not ideal.

Rep: I see. What kind of problems is that causing?

Buyer: Well, it's taking longer than it should. Maybe {time_impact} extra per week.

Rep: That's frustrating. Have you thought about what that means for your team's productivity?

Buyer: Yeah, it definitely slows us down. We could probably get more done without these issues.

Rep: Makes sense. What would it mean if you could fix that problem?

Buyer: We'd be more efficient, I guess. Maybe we could take on {additional_work}.

Rep: Right. So our solution actually helps with {feature_1} and {feature_2}. Would that be interesting to you?

Buyer: Potentially. I'd need to see how it works.

Rep: Sure, I can show you a demo. We've worked with companies like {similar_company}. When would be a good time?

Buyer: Let me check my calendar. Maybe next week?

Rep: Sounds good. I'll send you some information and we can schedule that demo...""",

        """Rep: Hello {buyer_name}, this is {rep_name} from {rep_company}. How are you today?

Buyer: I'm good. What's this call regarding?

Rep: I wanted to discuss your {process} setup. We help companies improve their {outcome}.

Buyer: Okay, we do have some challenges in that area.

Rep: What are you currently using?

Buyer: We use {current_tool} mainly, but it has limitations.

Rep: What kind of limitations?

Buyer: It doesn't handle {use_case} very well. Causes some headaches.

Rep: I understand. Is that impacting your team?

Buyer: Yeah, somewhat. We lose some time dealing with it. Probably {time_impact} a week or so.

Rep: That adds up. Have you calculated the cost of that?

Buyer: Not exactly, but it's definitely not efficient.

Rep: Right. If you could solve that, what would improve?

Buyer: We'd save time, probably get better {business_metric}.

Rep: Our solution offers {feature_1}, {feature_2}, and {feature_3}. Would any of those help?

Buyer: Maybe. I'd have to evaluate it properly.

Rep: Of course. Would you be interested in seeing a demo?

Buyer: Possibly. Send me some info first and we can go from there.

Rep: Will do. I'll email you today with details...""",
    ],

    "low": [
        """Rep: Hello, is this {buyer_name}?

Buyer: Yes, who's this?

Rep: This is {rep_name} from {rep_company}. We provide {product_category}. Do you have time to talk?

Buyer: I'm pretty busy. What's this about?

Rep: Well, we have a solution that can help with {general_benefit}. Are you interested?

Buyer: I don't know. What exactly do you do?

Rep: We help companies with {vague_description}. It's really great.

Buyer: How does it work?

Rep: It's a platform that does {feature_list}. Lots of companies use it.

Buyer: Okay. Are you familiar with what we do here?

Rep: Um, I know you're in the {industry} industry, right?

Buyer: Yes, but we have specific needs around {specific_need}.

Rep: Oh sure, we can definitely help with that. Our product has lots of features.

Buyer: Like what specifically?

Rep: Well, there's {feature_1} and {feature_2} and other things. It's really customizable.

Buyer: What would this cost?

Rep: It depends on your needs. We have different packages. Can I send you some information?

Buyer: I guess. But I'm not sure this is the right fit for us.

Rep: I think you'll be impressed once you see it. Can we schedule a demo?

Buyer: Maybe. Send the info first and I'll see.

Rep: Great! I'll get that over to you. When should I follow up?

Buyer: I'll reach out if I'm interested.

Rep: Okay, but I'll probably check in next week anyway...""",

        """Rep: Hi there, {buyer_name}? This is {rep_name}.

Buyer: Yes, hello.

Rep: I'm calling from {rep_company}. We work with companies in {industry}. How's business?

Buyer: It's fine. What can I help you with?

Rep: I wanted to tell you about our {product_category} solution. Do you use anything like that now?

Buyer: We have some tools, yes.

Rep: Are they working well?

Buyer: They're adequate for our needs currently.

Rep: Oh. Well, our solution is really powerful. It has {feature_1} and {feature_2}.

Buyer: Those sound like standard features to me.

Rep: Yes, but ours is better. We have lots of happy customers.

Buyer: What makes it better?

Rep: It's just more advanced. And easier to use. Companies love it.

Buyer: Can you be more specific?

Rep: Well, it saves time and improves efficiency.

Buyer: How much time? What efficiency gains?

Rep: It varies by customer, but it's significant.

Buyer: I see. What's the pricing?

Rep: We have competitive pricing. It depends on what you need.

Buyer: This is pretty vague. Do you have concrete information?

Rep: Yes, absolutely. I can send you our brochure. Can we schedule a call next week to discuss?

Buyer: I don't think so. If we're interested, we'll reach out.

Rep: Are you sure? I think this could really help you.

Buyer: I need to go. Thanks for calling...""",
    ],
}

# Buyer profiles for realistic conversations
BUYER_PROFILES = [
    {"name": "Jennifer Smith", "title": "VP of Operations", "company": "Acme Corp", "industry": "Manufacturing"},
    {"name": "Michael Johnson", "title": "Director of IT", "company": "TechStart Inc", "industry": "Technology"},
    {"name": "Sarah Williams", "title": "COO", "company": "Global Logistics", "industry": "Logistics"},
    {"name": "David Brown", "title": "Head of Sales", "company": "SalesPro", "industry": "SaaS"},
    {"name": "Emily Davis", "title": "CFO", "company": "FinanceFirst", "industry": "Financial Services"},
    {"name": "Robert Miller", "title": "VP of Marketing", "company": "MarketLeaders", "industry": "Marketing"},
    {"name": "Lisa Anderson", "title": "CTO", "company": "CloudSystems", "industry": "Cloud Computing"},
    {"name": "James Wilson", "title": "Operations Manager", "company": "RetailCo", "industry": "Retail"},
]

# Variables for template filling
TEMPLATE_VARS = {
    "process": ["customer onboarding", "lead qualification", "inventory management", "order processing", "customer support"],
    "current_tool": ["Salesforce", "HubSpot", "Excel spreadsheets", "an in-house system", "multiple disconnected tools"],
    "team_size": ["15", "20", "30", "50", "25"],
    "pain_point": ["data entry errors", "slow response times", "lack of visibility", "manual reporting", "integration issues"],
    "time_impact": ["10", "15", "20", "25", "30"],
    "business_goal": ["hit our quarterly targets", "scale efficiently", "improve customer satisfaction", "reduce churn"],
    "missed_target": ["2 deals", "3 opportunities", "our Q3 goal", "our expansion plan"],
    "business_metric": ["customer NPS", "sales velocity", "operational efficiency", "profit margins"],
    "opportunity_1": ["expand into new markets", "launch the new product line", "increase deal size by 30%"],
    "opportunity_2": ["reduce customer acquisition cost", "improve win rates", "accelerate sales cycles"],
    "tool_1": ["Excel", "Monday.com", "Asana", "Jira", "an old CRM"],
    "tool_2": ["Google Sheets", "Slack", "email", "custom scripts", "Trello"],
    "threshold": ["500 transactions", "1000 customers", "100 deals", "50 projects"],
    "issue_1": ["data sync errors", "performance slowdowns", "missing information", "duplicate entries"],
    "issue_2": ["manual reconciliation", "team confusion", "delayed reports", "customer complaints"],
    "department": ["sales", "operations", "customer success", "finance"],
    "project": ["the Q4 launch", "our expansion plan", "the migration", "new features"],
    "metric": ["close rate", "customer satisfaction", "response time", "efficiency"],
    "percentage": ["15%", "20%", "25%", "30%"],
    "customer_segment": ["enterprise clients", "key accounts", "our biggest customer", "half our pipeline"],
    "revenue_impact": ["$500K", "$1M", "$2M", "significant"],
    "target_metric": ["95% uptime", "< 2 hour response time", "20% higher close rate", "zero errors"],
    "strategic_initiative": ["international expansion", "the new product", "enterprise tier", "partnership program"],
    "product_category": ["sales enablement", "workflow automation", "data management", "customer engagement"],
    "additional_work": ["more projects", "higher volume", "better results", "strategic initiatives"],
    "feature_1": ["automation", "reporting", "integrations", "analytics"],
    "feature_2": ["real-time updates", "customization", "collaboration tools", "mobile access"],
    "feature_3": ["security", "scalability", "API access", "white-labeling"],
    "similar_company": ["Microsoft", "Salesforce", "Adobe", "Oracle"],
    "outcome": ["efficiency", "revenue", "customer satisfaction", "team productivity"],
    "use_case": ["reporting", "forecasting", "collaboration", "data migration"],
    "general_benefit": ["increasing sales", "saving time", "improving efficiency", "cutting costs"],
    "vague_description": ["business optimization", "digital transformation", "process improvement", "sales excellence"],
    "feature_list": ["multiple features", "various tools", "everything you need", "comprehensive functionality"],
    "specific_need": ["compliance", "data security", "integration with legacy systems", "custom reporting"],
}


# ===== Helper Functions =====

def get_random_business_date(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random business day (Mon-Fri) between start and end dates."""
    while True:
        # Generate random date
        time_delta = end_date - start_date
        random_days = random.randint(0, time_delta.days)
        random_date = start_date + timedelta(days=random_days)

        # Check if it's a business day (Monday=0, Sunday=6)
        if random_date.weekday() < 5:  # Monday to Friday
            # Add random time during business hours (9 AM - 5 PM)
            hour = random.randint(9, 16)
            minute = random.randint(0, 59)
            return random_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


def generate_score_with_trending(
    base_range: Tuple[float, float],
    std_dev: float,
    month_index: int,  # 0, 1, 2 for Oct, Nov, Dec
    trend: str,  # "improving", "declining", "stable"
) -> float:
    """Generate a score with trending behavior over time."""
    min_score, max_score = base_range
    base_mean = (min_score + max_score) / 2

    # Apply trend adjustment
    if trend == "improving":
        # Improve by ~0.3 points over 3 months
        adjustment = month_index * 0.15
    elif trend == "declining":
        # Decline by ~0.3 points over 3 months
        adjustment = -month_index * 0.15
    else:  # stable
        # Small random variation only
        adjustment = random.uniform(-0.05, 0.05)

    # Generate score with normal distribution
    score = random.gauss(base_mean + adjustment, std_dev)

    # Clamp to valid range [1.0, 5.0] and original range
    score = max(1.0, min(5.0, score))
    score = max(min_score - std_dev, min(max_score + std_dev, score))

    # Round to 1 decimal place
    return round(score, 1)


def generate_assessment_scores(
    profile: Dict,
    month_index: int,
    rep_modifier: float = 0.0,
) -> Dict[str, float]:
    """
    Generate SPIN assessment scores for a conversation.

    Args:
        profile: Organization profile with dimension ranges
        month_index: 0, 1, 2 for Oct, Nov, Dec (for trending)
        rep_modifier: Individual rep performance modifier (-0.3 to +0.3)

    Returns:
        Dictionary with all 7 SPIN dimensions
    """
    scores = {}

    for dimension, base_range in profile["dimension_ranges"].items():
        # Adjust range based on rep modifier
        adjusted_range = (
            base_range[0] + rep_modifier,
            base_range[1] + rep_modifier,
        )

        score = generate_score_with_trending(
            adjusted_range,
            profile["std_dev"],
            month_index,
            profile["trend"],
        )

        scores[dimension] = score

    return scores


def generate_transcript_text(
    performance_level: str,
    buyer_profile: Dict,
    rep_name: str,
    rep_company: str,
) -> str:
    """Generate a realistic transcript based on performance level."""
    template = random.choice(TRANSCRIPT_TEMPLATES[performance_level])

    # Fill in buyer info
    text = template.replace("{buyer_name}", buyer_profile["name"])
    text = text.replace("{buyer_title}", buyer_profile["title"])
    text = text.replace("{buyer_company}", buyer_profile["company"])
    text = text.replace("{industry}", buyer_profile["industry"])
    text = text.replace("{rep_name}", rep_name)
    text = text.replace("{rep_company}", rep_company)

    # Fill in random variables
    for var_name, options in TEMPLATE_VARS.items():
        placeholder = "{" + var_name + "}"
        if placeholder in text:
            text = text.replace(placeholder, random.choice(options))

    return text


def generate_coaching_feedback(scores: Dict[str, float], composite_score: float) -> Dict:
    """Generate coaching feedback based on scores."""
    # Determine overall performance level
    if composite_score >= 4.0:
        summary = "Excellent performance demonstrating strong SPIN selling skills."
    elif composite_score >= 3.0:
        summary = "Good foundation with opportunities for improvement in key areas."
    else:
        summary = "Significant development needed in multiple SPIN dimensions."

    # Find strengths and weaknesses
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [dim for dim, score in sorted_scores[:2] if score >= 4.0]
    weaknesses = [dim for dim, score in sorted_scores[-2:] if score < 3.5]

    # Generate wins
    wins = []
    if strengths:
        wins.append(f"Strong performance in {', '.join(strengths)} demonstrates mastery")
    if composite_score >= 4.0:
        wins.append("Excellent rapport building and conversation flow")
    elif composite_score >= 3.0:
        wins.append("Good questioning technique and buyer engagement")

    # Generate gaps
    gaps = []
    if weaknesses:
        gaps.append(f"Focus needed on {', '.join(weaknesses)} to uncover deeper needs")
    if composite_score < 3.5:
        gaps.append("Work on asking more probing questions to understand impact")
    if "implication" in weaknesses:
        gaps.append("Strengthen implication questions to quantify business impact")

    # Generate next actions
    next_actions = []
    if weaknesses:
        next_actions.append(f"Practice {weaknesses[0]} questions using the SPIN framework")
    next_actions.append("Review call recording and identify missed opportunities")
    if composite_score < 3.5:
        next_actions.append("Shadow top performers to observe advanced techniques")

    return {
        "summary": summary,
        "wins": wins if wins else ["Completed the call and gathered basic information"],
        "gaps": gaps if gaps else ["Minor improvements possible"],
        "next_actions": next_actions,
    }


# ===== Main Seeding Functions =====

def clear_existing_data(db):
    """Clear all existing seed data."""
    print("🗑️  Clearing existing data...")

    # Delete in correct order due to foreign keys
    db.query(Assessment).delete()
    db.query(Transcript).delete()
    db.query(Representative).delete()
    db.query(Organization).filter(
        Organization.name.in_(ORG_PROFILES.keys())
    ).delete(synchronize_session=False)

    db.commit()
    print("   ✅ Existing data cleared")


def seed_organization(db, org_name: str, org_description: str) -> Organization:
    """Create an organization."""
    # Check if exists
    existing = db.query(Organization).filter(Organization.name == org_name).first()
    if existing:
        print(f"   ⏭️  Organization already exists: {org_name}")
        return existing

    org = Organization(
        name=org_name,
        description=org_description,
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    print(f"   ✅ Created organization: {org_name}")
    return org


def seed_user_for_org(db, organization: Organization, email: str) -> None:
    """Create or update a user for the organization."""
    password = "Password123!"
    full_name = f"{organization.name} Admin"

    existing = user_crud.get_by_email(db, email=email)
    if existing:
        # Update organization_id if it's different
        if existing.organization_id != organization.id:
            existing.organization_id = organization.id
            db.commit()
            print(f"      ✅ Updated user organization: {email}")
        else:
            print(f"      ⏭️  User already exists: {email}")
        print(f"      📋 Login: {email} / {password}")
        return

    user = user_crud.create(
        db,
        email=email,
        password=password,
        full_name=full_name,
        is_superuser=True,
        organization_id=organization.id,
    )

    print(f"      ✅ Created user: {email}")
    print(f"      📋 Login: {email} / {password}")


def seed_representatives(
    db,
    organization: Organization,
    names_list: List[Tuple[str, str, str]],
) -> List[Representative]:
    """Create representatives for an organization."""
    representatives = []

    # Base hire date for this org (stagger by 6 months intervals)
    base_hire_date = datetime(2023, 1, 1, tzinfo=timezone.utc)

    for i, (full_name, department, email) in enumerate(names_list):
        # Check if exists
        existing = rep_crud.get_by_email(db, email=email)
        if existing:
            representatives.append(existing)
            continue

        # Stagger hire dates
        hire_date = base_hire_date + timedelta(days=i * 60)

        rep = rep_crud.create(
            db,
            email=email,
            full_name=full_name,
            department=department,
            hire_date=hire_date,
            organization_id=organization.id,
        )
        representatives.append(rep)

    return representatives


def seed_transcripts_and_assessments(
    db,
    representatives: List[Representative],
    org_profile: Dict,
    org_name: str,
    conversations_per_month: int = 25,
) -> Tuple[int, int]:
    """
    Create transcripts and assessments for representatives.

    Returns:
        Tuple of (transcript_count, assessment_count)
    """
    # Determine performance level for template selection
    avg_composite = sum(org_profile["composite_range"]) / 2
    if avg_composite >= 4.0:
        performance_level = "high"
    elif avg_composite >= 3.0:
        performance_level = "medium"
    else:
        performance_level = "low"

    # Date ranges for 3 months (Oct, Nov, Dec 2025)
    months = [
        (datetime(2025, 10, 1, tzinfo=timezone.utc), datetime(2025, 10, 31, 23, 59, 59, tzinfo=timezone.utc), 0),
        (datetime(2025, 11, 1, tzinfo=timezone.utc), datetime(2025, 11, 30, 23, 59, 59, tzinfo=timezone.utc), 1),
        (datetime(2025, 12, 1, tzinfo=timezone.utc), datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc), 2),
    ]

    transcript_count = 0
    assessment_count = 0

    # Generate rep modifiers (some reps better/worse than org average)
    rep_modifiers = {}
    for rep in representatives:
        # Normal distribution around 0, range -0.4 to +0.4
        rep_modifiers[rep.id] = random.gauss(0, 0.2)
        rep_modifiers[rep.id] = max(-0.4, min(0.4, rep_modifiers[rep.id]))

    for rep in representatives:
        rep_modifier = rep_modifiers[rep.id]

        for start_date, end_date, month_index in months:
            # Generate conversations for this month
            for _ in range(conversations_per_month):
                # Random buyer and date
                buyer = random.choice(BUYER_PROFILES)
                call_date = get_random_business_date(start_date, end_date)

                # Generate transcript
                transcript_text = generate_transcript_text(
                    performance_level,
                    buyer,
                    rep.full_name.split()[0],  # First name
                    org_name,
                )

                # Create transcript
                transcript = Transcript(
                    representative_id=rep.id,
                    buyer_id=f"{buyer['company']}-{buyer['name'].replace(' ', '')}",
                    call_metadata={
                        "call_date": call_date.isoformat(),
                        "buyer_name": buyer["name"],
                        "buyer_title": buyer["title"],
                        "buyer_company": buyer["company"],
                        "buyer_industry": buyer["industry"],
                        "call_duration_minutes": random.randint(15, 45),
                    },
                    transcript=transcript_text,
                    created_at=call_date,
                )
                db.add(transcript)
                db.flush()  # Get transcript.id

                # Generate assessment scores
                scores = generate_assessment_scores(
                    org_profile,
                    month_index,
                    rep_modifier,
                )

                # Calculate composite score
                composite_score = round(sum(scores.values()) / len(scores), 1)

                # Generate coaching feedback
                coaching = generate_coaching_feedback(scores, composite_score)

                # Create assessment
                assessment = Assessment(
                    transcript_id=transcript.id,
                    scores=scores,
                    coaching=coaching,
                    model_name="gpt-4o-mini",
                    prompt_version="spin_v1",
                    latency_ms=random.randint(800, 2000),
                    created_at=call_date,
                )
                db.add(assessment)

                transcript_count += 1
                assessment_count += 1

        # Commit after each rep to avoid huge transactions
        db.commit()

    return transcript_count, assessment_count


def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="Seed varied organization data")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before seeding")
    args = parser.parse_args()

    db = SessionLocal()

    try:
        print("🌱 Starting varied organization seeding...\n")

        if args.clear:
            clear_existing_data(db)
            print()

        # Seed each organization
        total_transcripts = 0
        total_assessments = 0
        user_credentials = []

        for org_name, profile in ORG_PROFILES.items():
            print(f"🏢 Seeding organization: {org_name}")
            print(f"   Profile: {profile['description']}")
            print(f"   Composite range: {profile['composite_range']}")
            print(f"   Trend: {profile['trend']}")

            # Create organization
            org = seed_organization(db, org_name, profile["description"])

            # Create user for organization
            print(f"   Creating user account...")
            seed_user_for_org(db, org, profile["user_email"])
            user_credentials.append((profile["user_email"], "Password123!"))

            # Create prompt template
            existing_templates = template_crud.get_by_org(db, org.id)
            if not existing_templates:
                template_crud.create_default_for_org(db, org.id)

            # Create representatives
            print(f"   Creating {len(REP_NAMES[org_name])} representatives...")
            reps = seed_representatives(db, org, REP_NAMES[org_name])
            print(f"   ✅ Created/found {len(reps)} representatives")

            # Create transcripts and assessments
            print(f"   Generating conversations (25 per rep per month for 3 months)...")
            t_count, a_count = seed_transcripts_and_assessments(
                db, reps, profile, org_name, conversations_per_month=25
            )
            total_transcripts += t_count
            total_assessments += a_count

            print(f"   ✅ Created {t_count} transcripts and {a_count} assessments")
            print()

        # Final summary
        print("=" * 60)
        print("✨ Seeding complete! All test data is ready.")
        print("=" * 60)
        print(f"\n📊 Summary:")
        print(f"   Organizations: {len(ORG_PROFILES)}")
        print(f"   Representatives: {sum(len(names) for names in REP_NAMES.values())}")
        print(f"   Transcripts: {total_transcripts}")
        print(f"   Assessments: {total_assessments}")
        print(f"\n🔐 User Login Credentials:")
        for email, password in user_credentials:
            print(f"   {email} / {password}")
        print()

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
