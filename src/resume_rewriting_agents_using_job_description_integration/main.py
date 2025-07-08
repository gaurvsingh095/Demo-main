# #!/usr/bin/env python
# import sys
# # from resume_rewriting_agents_using_job_description_integration.crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew


# # This main file is intended to be a way for your to run your
# # crew locally, so refrain from adding unnecessary logic into this file.
# # Replace with inputs you want to test with, it will automatically
# # interpolate any tasks and agents information

# def get_resume_text():
#     """
#     Get resume text from user input.
#     """
#     print("Please paste your resume text below (press Ctrl+D or Ctrl+Z when finished):")
#     lines = []
#     try:
#         while True:
#             line = input()
#             lines.append(line)
#     except EOFError:
#         pass
#     return '\n'.join(lines)

# def get_job_description_url():
#     """
#     Get job description URL from user input.
#     """
#     print("Please enter the job description URL:")
#     return input().strip()

# def run():
#     """
#     Run the crew.
#     """
#     # Get resume text from user input
#     resume_text = get_resume_text()
    
#     # Get job description URL from user input
#     job_description_url = get_job_description_url()
    
#     inputs = {
#         'resume_text': resume_text,
#         'job_description_url': job_description_url
#     }
#     ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew().kickoff(inputs=inputs)


# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     # Get resume text from user input
#     resume_text = get_resume_text()
    
#     # Get job description URL from user input
#     job_description_url = get_job_description_url()
    
#     inputs = {
#         'resume_text': resume_text,
#         'job_description_url': job_description_url
#     }
#     try:
#         ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew().replay(task_id=sys.argv[1])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     # Get resume text from user input
#     resume_text = get_resume_text()
    
#     # Get job description URL from user input
#     job_description_url = get_job_description_url()
    
#     inputs = {
#         'resume_text': resume_text,
#         'job_description_url': job_description_url
#     }
#     try:
#         ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: main.py <command> [<args>]")
#         sys.exit(1)

#     command = sys.argv[1]
#     if command == "run":
#         run()
#     elif command == "train":
#         train()
#     elif command == "replay":
#         replay()
#     elif command == "test":
#         test()
#     else:
#         print(f"Unknown command: {command}")
#         sys.exit(1)

#!/usr/bin/env python
import sys
import argparse
from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew


def get_resume_text_interactive():
    """
    Prompt user to paste resume text interactively.
    """
    print("Please paste your resume text below (press Ctrl+D or Ctrl+Z when finished):")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return '\n'.join(lines)


def get_job_description_url_interactive():
    """
    Prompt user to enter job description URL interactively.
    """
    print("Please enter the job description URL:")
    return input().strip()


def main():
    parser = argparse.ArgumentParser(
        description="Run or manage the Resume Rewriting Crew with optional non-interactive inputs."
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # run command parser
    run_parser = subparsers.add_parser('run', help='Execute the crew with a resume and job URL')
    resume_group = run_parser.add_mutually_exclusive_group()
    resume_group.add_argument('-r', '--resume', help='Resume text (wrap in quotes if contains newlines)')
    resume_group.add_argument('--resume-file', type=argparse.FileType('r', encoding='utf-8'),
                              help='Path to file containing resume text')
    run_parser.add_argument('-u', '--url', help='Job description URL')

    # train command parser
    train_parser = subparsers.add_parser('train', help='Train the crew')
    train_parser.add_argument('n_iterations', type=int, help='Number of training iterations')
    train_parser.add_argument('filename', help='Filename to save training results')
    resume_group = train_parser.add_mutually_exclusive_group()
    resume_group.add_argument('-r', '--resume', help='Resume text')
    resume_group.add_argument('--resume-file', type=argparse.FileType('r', encoding='utf-8'),
                              help='Path to file containing resume text')
    train_parser.add_argument('-u', '--url', help='Job description URL')

    # replay command parser
    replay_parser = subparsers.add_parser('replay', help='Replay a completed task by ID')
    replay_parser.add_argument('task_id', help='ID of the task to replay')

    # test command parser
    test_parser = subparsers.add_parser('test', help='Test the crew execution')
    test_parser.add_argument('n_iterations', type=int, help='Number of test iterations')
    test_parser.add_argument('openai_model_name', help='OpenAI model name to use')
    resume_group = test_parser.add_mutually_exclusive_group()
    resume_group.add_argument('-r', '--resume', help='Resume text')
    resume_group.add_argument('--resume-file', type=argparse.FileType('r', encoding='utf-8'),
                              help='Path to file containing resume text')
    test_parser.add_argument('-u', '--url', help='Job description URL')

    args = parser.parse_args()

    # Helper to get resume text
    def _get_resume_text():
        if getattr(args, 'resume_file', None):
            return args.resume_file.read()
        elif getattr(args, 'resume', None):
            return args.resume
        else:
            return get_resume_text_interactive()

    # Helper to get URL
    def _get_url():
        if getattr(args, 'url', None):
            return args.url
        else:
            return get_job_description_url_interactive()

    crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()

    if args.command == 'run':
        inputs = {
            'resume_text': _get_resume_text(),
            'job_description_url': _get_url()
        }
        crew.kickoff(inputs=inputs)

    elif args.command == 'train':
        inputs = {
            'resume_text': _get_resume_text(),
            'job_description_url': _get_url()
        }
        crew.train(n_iterations=args.n_iterations, filename=args.filename, inputs=inputs)

    elif args.command == 'replay':
        crew.replay(task_id=args.task_id)

    elif args.command == 'test':
        inputs = {
            'resume_text': _get_resume_text(),
            'job_description_url': _get_url()
        }
        crew.test(n_iterations=args.n_iterations, openai_model_name=args.openai_model_name, inputs=inputs)

if __name__ == '__main__':
    main()
