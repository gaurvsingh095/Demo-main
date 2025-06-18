from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import PDFSearchTool
from crewai_tools import DOCXSearchTool
from crewai_tools import TXTSearchTool
from crewai_tools import ScrapeWebsiteTool

@CrewBase
class ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew():
    """ResumeRewritingAgentsUsingJobDescriptionIntegration crew"""

    @agent
    def resume_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_extractor'],
            tools=[],
        )

    @agent
    def job_description_scraper(self) -> Agent:
        return Agent(
            config=self.agents_config['job_description_scraper'],
            tools=[ScrapeWebsiteTool()],
        )

    @agent
    def resume_rewriter(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_rewriter'],
            tools=[],
        )


    @task
    def extract_resume_information(self) -> Task:
        return Task(
            config=self.tasks_config['extract_resume_information'],
            tools=[],
        )

    @task
    def scrape_job_description(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_job_description'],
            tools=[ScrapeWebsiteTool()],
        )

    @task
    def rewrite_resume(self) -> Task:
        return Task(
            config=self.tasks_config['rewrite_resume'],
            
        )


    @crew
    def crew(self) -> Crew:
        """Creates the ResumeRewritingAgentsUsingJobDescriptionIntegration crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
