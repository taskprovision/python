#!/usr/bin/env python3
"""
TaskProvision GitHub Lead Mining
Automated lead generation from GitHub repositories
"""

import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GitHubLead:
    """GitHub lead data structure"""
    repo_name: str
    owner: str
    owner_type: str  # User or Organization
    email: Optional[str]
    company: Optional[str]
    location: Optional[str]
    languages: List[str]
    stars: int
    issues: int
    last_updated: str
    has_ai_keywords: bool
    contributors_count: int
    score: float

class GitHubLeadMiner:
    """Automated GitHub lead mining system"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.session = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = None
        
        # AI/ML keywords for targeting
        self.ai_keywords = [
            'machine learning', 'artificial intelligence', 'deep learning',
            'neural network', 'tensorflow', 'pytorch', 'scikit-learn',
            'nlp', 'computer vision', 'data science', 'llm', 'transformer',
            'automation', 'ai', 'ml', 'chatbot', 'recommendation'
        ]
        
        # Target criteria
        self.target_criteria = {
            'min_stars': 10,
            'max_stars': 10000,  # Avoid massive projects
            'min_contributors': 2,
            'max_contributors': 50,  # Small to medium teams
            'languages': ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust'],
            'updated_since_days': 30
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'TaskProvision-LeadMiner/1.0'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_rate_limit(self):
        """Check and respect GitHub API rate limits"""
        if self.rate_limit_remaining <= 100:
            if self.rate_limit_reset:
                wait_time = self.rate_limit_reset - time.time()
                if wait_time > 0:
                    logger.warning(f"Rate limit low, waiting {wait_time:.0f} seconds")
                    await asyncio.sleep(wait_time + 1)
    
    async def search_repositories(self, query: str, per_page: int = 100) -> List[Dict]:
        """Search GitHub repositories with given query"""
        await self.check_rate_limit()
        
        url = f"{self.base_url}/search/repositories"
        params = {
            'q': query,
            'sort': 'updated',
            'order': 'desc',
            'per_page': per_page
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                # Update rate limit info
                self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))
                
                if response.status == 200:
                    data = await response.json()
                    return data.get('items', [])
                elif response.status == 403:
                    logger.error("Rate limit exceeded")
                    return []
                else:
                    logger.error(f"GitHub API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error searching repositories: {e}")
            return []
    
    async def get_user_details(self, username: str) -> Optional[Dict]:
        """Get detailed user information"""
        await self.check_rate_limit()
        
        url = f"{self.base_url}/users/{username}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Error getting user details for {username}: {e}")
            return None
    
    async def get_repository_languages(self, owner: str, repo: str) -> List[str]:
        """Get programming languages used in repository"""
        await self.check_rate_limit()
        
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    languages = await response.json()
                    return list(languages.keys())
                return []
        except Exception as e:
            logger.error(f"Error getting languages for {owner}/{repo}: {e}")
            return []
    
    async def get_contributors_count(self, owner: str, repo: str) -> int:
        """Get number of contributors"""
        await self.check_rate_limit()
        
        url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
        params = {'per_page': 1, 'anon': 'false'}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # Get count from Link header
                    link_header = response.headers.get('Link', '')
                    if 'rel="last"' in link_header:
                        # Parse last page number
                        import re
                        match = re.search(r'page=(\d+)>; rel="last"', link_header)
                        if match:
                            return int(match.group(1))
                    
                    # Fallback: count actual contributors
                    contributors = await response.json()
                    return len(contributors)
                return 0
        except Exception as e:
            logger.error(f"Error getting contributors for {owner}/{repo}: {e}")
            return 0
    
    def check_ai_relevance(self, repo_data: Dict) -> bool:
        """Check if repository is AI/ML related"""
        text_to_check = f"{repo_data.get('description', '')} {repo_data.get('name', '')}".lower()
        
        for keyword in self.ai_keywords:
            if keyword in text_to_check:
                return True
        
        # Check topics
        topics = repo_data.get('topics', [])
        ai_topics = {'machine-learning', 'artificial-intelligence', 'deep-learning', 
                     'neural-networks', 'ai', 'ml', 'nlp', 'computer-vision'}
        return bool(set(topics) & ai_topics)
    
    def calculate_lead_score(self, lead: GitHubLead) -> float:
        """Calculate lead quality score (0-100)"""
        score = 0
        
        # Star rating (0-30 points)
        if lead.stars >= 100:
            score += 30
        elif lead.stars >= 50:
            score += 25
        elif lead.stars >= 20:
            score += 20
        elif lead.stars >= 10:
            score += 15
        
        # Recent activity (0-25 points)
        try:
            last_update = datetime.fromisoformat(lead.last_updated.replace('Z', '+00:00'))
            days_ago = (datetime.now().astimezone() - last_update).days
            if days_ago <= 7:
                score += 25
            elif days_ago <= 30:
                score += 20
            elif days_ago <= 90:
                score += 15
        except:
            pass
        
        # Team size (0-20 points)
        if 3 <= lead.contributors_count <= 15:
            score += 20
        elif 2 <= lead.contributors_count <= 25:
            score += 15
        elif lead.contributors_count >= 2:
            score += 10
        
        # AI relevance (0-15 points)
        if lead.has_ai_keywords:
            score += 15
        
        # Issues indicate active development (0-10 points)
        if 5 <= lead.issues <= 50:
            score += 10
        elif 1 <= lead.issues <= 100:
            score += 5
        
        return min(score, 100)
    
    async def process_repository(self, repo_data: Dict) -> Optional[GitHubLead]:
        """Process repository data into lead"""
        try:
            owner = repo_data['owner']['login']
            repo_name = repo_data['name']
            
            # Get additional data
            user_details = await self.get_user_details(owner)
            languages = await self.get_repository_languages(owner, repo_name)
            contributors_count = await self.get_contributors_count(owner, repo_name)
            
            # Filter by criteria
            if repo_data['stargazers_count'] < self.target_criteria['min_stars']:
                return None
            
            if repo_data['stargazers_count'] > self.target_criteria['max_stars']:
                return None
            
            if contributors_count < self.target_criteria['min_contributors']:
                return None
            
            if contributors_count > self.target_criteria['max_contributors']:
                return None
            
            # Check if uses target languages
            target_langs = set(self.target_criteria['languages'])
            repo_langs = set(languages)
            if not (target_langs & repo_langs):
                return None
            
            # Create lead
            lead = GitHubLead(
                repo_name=repo_name,
                owner=owner,
                owner_type=repo_data['owner']['type'],
                email=user_details.get('email') if user_details else None,
                company=user_details.get('company') if user_details else None,
                location=user_details.get('location') if user_details else None,
                languages=languages,
                stars=repo_data['stargazers_count'],
                issues=repo_data['open_issues_count'],
                last_updated=repo_data['updated_at'],
                has_ai_keywords=self.check_ai_relevance(repo_data),
                contributors_count=contributors_count,
                score=0  # Will be calculated
            )
            
            # Calculate score
            lead.score = self.calculate_lead_score(lead)
            
            return lead
            
        except Exception as e:
            logger.error(f"Error processing repository {repo_data.get('name', 'unknown')}: {e}")
            return None
    
    async def mine_leads(self, max_leads: int = 1000) -> List[GitHubLead]:
        """Mine GitHub leads based on criteria"""
        leads = []
        
        # Search queries for different target types
        search_queries = [
            f"language:Python stars:{self.target_criteria['min_stars']}..{self.target_criteria['max_stars']} pushed:>2024-11-01",
            f"language:JavaScript machine learning stars:{self.target_criteria['min_stars']}..{self.target_criteria['max_stars']}",
            f"language:Python AI automation stars:{self.target_criteria['min_stars']}..{self.target_criteria['max_stars']}",
            f"language:TypeScript api automation stars:{self.target_criteria['min_stars']}..{self.target_criteria['max_stars']}",
            f"language:Go microservice automation stars:{self.target_criteria['min_stars']}..{self.target_criteria['max_stars']}",
        ]
        
        for query in search_queries:
            if len(leads) >= max_leads:
                break
                
            logger.info(f"Searching with query: {query}")
            repos = await self.search_repositories(query)
            
            for repo_data in repos:
                if len(leads) >= max_leads:
                    break
                
                lead = await self.process_repository(repo_data)
                if lead and lead.score >= 50:  # Only high-quality leads
                    leads.append(lead)
                    logger.info(f"Found lead: {lead.owner}/{lead.repo_name} (score: {lead.score:.1f})")
            
            # Rate limiting pause
            await asyncio.sleep(1)
        
        # Sort by score
        leads.sort(key=lambda x: x.score, reverse=True)
        
        return leads
    
    def save_leads(self, leads: List[GitHubLead], filename: str = None):
        """Save leads to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_leads_{timestamp}.json"
        
        leads_data = []
        for lead in leads:
            lead_dict = {
                'repo_name': lead.repo_name,
                'owner': lead.owner,
                'owner_type': lead.owner_type,
                'email': lead.email,
                'company': lead.company,
                'location': lead.location,
                'languages': lead.languages,
                'stars': lead.stars,
                'issues': lead.issues,
                'last_updated': lead.last_updated,
                'has_ai_keywords': lead.has_ai_keywords,
                'contributors_count': lead.contributors_count,
                'score': lead.score,
                'github_url': f"https://github.com/{lead.owner}/{lead.repo_name}",
                'contact_priority': 'high' if lead.score >= 80 else 'medium' if lead.score >= 60 else 'low'
            }
            leads_data.append(lead_dict)
        
        with open(filename, 'w') as f:
            json.dump(leads_data, f, indent=2)
        
        logger.info(f"Saved {len(leads)} leads to {filename}")
        return filename
    
    def generate_outreach_data(self, leads: List[GitHubLead]) -> List[Dict]:
        """Generate personalized outreach data"""
        outreach_data = []
        
        for lead in leads:
            # Analyze repository for pain points
            pain_points = []
            
            if lead.issues > 20:
                pain_points.append(f"{lead.issues} open issues suggest technical debt")
            
            if 'JavaScript' in lead.languages and 'TypeScript' not in lead.languages:
                pain_points.append("JavaScript project could benefit from TypeScript migration")
            
            if lead.has_ai_keywords:
                pain_points.append("AI/ML project could benefit from automated code quality")
            
            # Generate personalized message
            message_template = f"""
Hi {lead.owner},

I noticed your {lead.repo_name} project on GitHub - impressive work with {', '.join(lead.languages[:2])}!

I saw that you have {lead.issues} open issues and {lead.contributors_count} contributors. 
Many teams like yours save 4-6 hours/week using TaskProvision's AI-powered development automation.

Would you be interested in a 15-minute demo showing how we could:
- Automatically fix common code issues
- Generate high-quality tests
- Streamline your development workflow

Free health check of your repository: https://taskprovision.com/tools/repo-health?repo={lead.owner}/{lead.repo_name}

Best regards,
TaskProvision Team
            """.strip()
            
            outreach_data.append({
                'lead': lead,
                'pain_points': pain_points,
                'message': message_template,
                'priority': 'high' if lead.score >= 80 else 'medium' if lead.score >= 60 else 'low'
            })
        
        return outreach_data

async def main():
    """Main lead mining execution"""
    if not os.getenv('GITHUB_TOKEN'):
        logger.error("GITHUB_TOKEN environment variable required")
        return
    
    async with GitHubLeadMiner() as miner:
        logger.info("Starting GitHub lead mining...")
        
        # Mine leads
        leads = await miner.mine_leads(max_leads=500)
        
        if leads:
            # Save leads
            filename = miner.save_leads(leads)
            
            # Generate outreach data
            outreach_data = miner.generate_outreach_data(leads[:50])  # Top 50 for outreach
            
            # Save outreach data
            outreach_filename = filename.replace('leads_', 'outreach_')
            with open(outreach_filename, 'w') as f:
                outreach_list = []
                for item in outreach_data:
                    outreach_list.append({
                        'owner': item['lead'].owner,
                        'repo': item['lead'].repo_name,
                        'email': item['lead'].email,
                        'score': item['lead'].score,
                        'priority': item['priority'],
                        'pain_points': item['pain_points'],
                        'message': item['message']
                    })
                json.dump(outreach_list, f, indent=2)
            
            logger.info(f"Generated outreach data for {len(outreach_data)} leads")
            
            # Summary
            print(f"\n📊 Lead Mining Summary:")
            print(f"Total leads found: {len(leads)}")
            print(f"High priority (80+): {len([l for l in leads if l.score >= 80])}")
            print(f"Medium priority (60-79): {len([l for l in leads if 60 <= l.score < 80])}")
            print(f"Low priority (50-59): {len([l for l in leads if 50 <= l.score < 60])}")
            print(f"\nTop 5 leads:")
            for i, lead in enumerate(leads[:5], 1):
                print(f"{i}. {lead.owner}/{lead.repo_name} - Score: {lead.score:.1f}")
        else:
            logger.warning("No leads found")

if __name__ == "__main__":
    asyncio.run(main())