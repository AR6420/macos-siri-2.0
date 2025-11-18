#!/usr/bin/env python3
"""
Demo script for Enhanced Inline AI feature.

Demonstrates all features with mock responses for development/testing.
Can run without UI for integration testing.
"""

import asyncio
import json
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DemoScenario:
    """Demo scenario configuration"""
    name: str
    description: str
    action: str
    input_text: str
    params: Dict[str, Any] = None
    expected_output: str = ""


# ============================================================================
# DEMO SCENARIOS
# ============================================================================

DEMO_SCENARIOS = [
    # Proofread
    DemoScenario(
        name="Proofread Email",
        description="Fix spelling and grammar errors in a casual email",
        action="proofread",
        input_text="Hey john, I hope your doing well. I wanted to touch base about the project we discused yesterday.",
        expected_output="Hey John, I hope you're doing well. I wanted to touch base about the project we discussed yesterday."
    ),

    # Rewrite - Friendly
    DemoScenario(
        name="Rewrite to Friendly Tone",
        description="Convert formal text to friendly tone",
        action="rewrite",
        input_text="I am writing to formally request your assistance with this matter.",
        params={"tone": "friendly"},
        expected_output="Hey! I'd love to get your help with this."
    ),

    # Rewrite - Professional
    DemoScenario(
        name="Rewrite to Professional Tone",
        description="Convert casual text to professional tone",
        action="rewrite",
        input_text="Hey, can you fix that bug ASAP?",
        params={"tone": "professional"},
        expected_output="Could you please address the reported issue at your earliest convenience?"
    ),

    # Rewrite - Concise
    DemoScenario(
        name="Make More Concise",
        description="Shorten verbose text",
        action="rewrite",
        input_text="In my personal opinion, I think that perhaps we might want to consider the possibility of implementing this feature.",
        params={"style": "concise"},
        expected_output="Let's implement this feature."
    ),

    # Summarize
    DemoScenario(
        name="Summarize Article",
        description="Summarize a long article into key points",
        action="summarize",
        input_text="""
Artificial intelligence has made remarkable progress in recent years, transforming industries
from healthcare to transportation. Machine learning algorithms can now diagnose diseases,
drive cars, and even create art. However, these advances also raise important ethical
questions about privacy, bias, and the future of work. As AI systems become more powerful,
society must grapple with how to ensure they are developed and deployed responsibly.
        """,
        expected_output="AI has advanced significantly, transforming industries but raising ethical concerns about privacy, bias, and employment."
    ),

    # Key Points
    DemoScenario(
        name="Extract Key Points",
        description="Extract key points from meeting notes",
        action="key_points",
        input_text="""
The new feature will improve user experience by reducing load times and simplifying navigation.
It requires backend changes to the API and frontend updates to the dashboard.
We estimate 3 weeks of development time and 1 week of testing.
The feature should increase user engagement by 20%.
        """,
        expected_output="""• Improves UX via faster load times and simpler navigation
• Requires backend API and frontend dashboard changes
• 3 weeks dev + 1 week testing
• Expected 20% engagement increase"""
    ),

    # Make List
    DemoScenario(
        name="Convert to Bullet List",
        description="Convert paragraph to bullet list",
        action="make_list",
        input_text="We need to buy milk, eggs, bread, butter, cheese, and yogurt from the store.",
        expected_output="""• Milk
• Eggs
• Bread
• Butter
• Cheese
• Yogurt"""
    ),

    # Make Numbered List
    DemoScenario(
        name="Convert to Numbered List",
        description="Convert instructions to numbered list",
        action="make_numbered_list",
        input_text="First, analyze requirements. Second, design solution. Third, implement. Fourth, test thoroughly.",
        expected_output="""1. Analyze requirements
2. Design solution
3. Implement
4. Test thoroughly"""
    ),

    # Make Table
    DemoScenario(
        name="Convert to Table",
        description="Convert data to markdown table",
        action="make_table",
        input_text="Product A costs $10 and sold 100 units. Product B costs $20 and sold 50 units.",
        expected_output="""| Product | Price | Units Sold |
|---------|-------|------------|
| A       | $10   | 100        |
| B       | $20   | 50         |"""
    ),

    # Compose
    DemoScenario(
        name="Compose Thank You Email",
        description="Compose email from prompt",
        action="compose",
        input_text="Write a thank you email to John for the meeting yesterday and confirm we'll send the proposal by Friday",
        expected_output="""Hi John,

Thank you for taking the time to meet yesterday. I appreciated your insights on the project timeline.

As we discussed, I'll draft the initial specification by Friday and share it with the team.

Best regards"""
    ),
]


# ============================================================================
# DEMO RUNNER
# ============================================================================

class InlineAIDemo:
    """Demo runner for inline AI features"""

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode

    async def run_scenario(self, scenario: DemoScenario) -> Dict[str, Any]:
        """Run a single demo scenario"""

        print(f"\n{'=' * 70}")
        print(f"SCENARIO: {scenario.name}")
        print(f"{'=' * 70}")
        print(f"\nDescription: {scenario.description}")
        print(f"\nAction: {scenario.action}")
        if scenario.params:
            print(f"Parameters: {json.dumps(scenario.params, indent=2)}")

        print(f"\n--- INPUT ---")
        print(scenario.input_text.strip())

        # Simulate processing
        if self.mock_mode:
            result = self._mock_process(scenario)
        else:
            # Would call actual handler here
            result = await self._real_process(scenario)

        print(f"\n--- OUTPUT ---")
        if result["status"] == "success":
            print(result["result"]["text"])
        else:
            print(f"ERROR: {result['message']}")

        print(f"\n{'=' * 70}\n")

        return result

    def _mock_process(self, scenario: DemoScenario) -> Dict[str, Any]:
        """Mock processing for demo"""

        # Simulate different response times
        import time
        time.sleep(0.5)  # Simulate LLM latency

        return {
            "status": "success",
            "result": {
                "text": scenario.expected_output.strip(),
                "original": scenario.input_text.strip(),
                "action": scenario.action,
                "latency_ms": 500
            }
        }

    async def _real_process(self, scenario: DemoScenario) -> Dict[str, Any]:
        """Real processing using actual handler"""

        from voice_assistant.inline_ai.enhanced_handler import EnhancedInlineAIHandler
        from voice_assistant.llm.factory import ProviderFactory

        # Create handler with real LLM
        llm = ProviderFactory.create("local_gpt_oss", {})
        handler = EnhancedInlineAIHandler(llm)

        # Build command
        command = {
            "action": scenario.action,
            "text": scenario.input_text
        }
        if scenario.params:
            command["params"] = scenario.params

        # Execute
        result = await handler.handle_command(command)
        return result

    async def run_all_scenarios(self):
        """Run all demo scenarios"""

        print("\n" + "=" * 70)
        print("ENHANCED INLINE AI - FEATURE DEMO")
        print("=" * 70)
        print(f"\nRunning {len(DEMO_SCENARIOS)} demo scenarios...")
        print(f"Mode: {'MOCK' if self.mock_mode else 'REAL'}")

        results = []
        for scenario in DEMO_SCENARIOS:
            result = await self.run_scenario(scenario)
            results.append({
                "scenario": scenario.name,
                "status": result["status"],
                "success": result["status"] == "success"
            })

        # Summary
        print("\n" + "=" * 70)
        print("DEMO SUMMARY")
        print("=" * 70)

        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)

        print(f"\nCompleted: {total_count}/{total_count} scenarios")
        print(f"Successful: {success_count}/{total_count}")

        if success_count == total_count:
            print("\n✓ All scenarios completed successfully!")
        else:
            print(f"\n✗ {total_count - success_count} scenarios failed")

            for r in results:
                if not r["success"]:
                    print(f"  - {r['scenario']}: {r['status']}")

    async def run_interactive_demo(self):
        """Interactive demo mode"""

        print("\n" + "=" * 70)
        print("ENHANCED INLINE AI - INTERACTIVE DEMO")
        print("=" * 70)

        while True:
            print("\nAvailable scenarios:")
            for i, scenario in enumerate(DEMO_SCENARIOS, 1):
                print(f"  {i}. {scenario.name}")

            print(f"  {len(DEMO_SCENARIOS) + 1}. Run all scenarios")
            print("  0. Exit")

            try:
                choice = int(input("\nSelect scenario: "))

                if choice == 0:
                    print("\nExiting demo. Goodbye!")
                    break
                elif choice == len(DEMO_SCENARIOS) + 1:
                    await self.run_all_scenarios()
                elif 1 <= choice <= len(DEMO_SCENARIOS):
                    await self.run_scenario(DEMO_SCENARIOS[choice - 1])
                else:
                    print("Invalid choice. Please try again.")

            except (ValueError, KeyboardInterrupt):
                print("\nExiting demo. Goodbye!")
                break

    async def run_custom_scenario(self, action: str, text: str, params: Dict = None):
        """Run custom scenario"""

        scenario = DemoScenario(
            name="Custom Scenario",
            description=f"Custom {action} operation",
            action=action,
            input_text=text,
            params=params or {}
        )

        return await self.run_scenario(scenario)


# ============================================================================
# WORKFLOW DEMOS
# ============================================================================

class WorkflowDemo:
    """Demo complete workflows"""

    def __init__(self):
        self.demo = InlineAIDemo(mock_mode=True)

    async def email_writing_workflow(self):
        """Demo: Complete email writing workflow"""

        print("\n" + "=" * 70)
        print("WORKFLOW DEMO: Email Writing")
        print("=" * 70)

        # Step 1: Compose draft
        print("\n📝 Step 1: Compose initial draft")
        draft_result = await self.demo.run_custom_scenario(
            action="compose",
            text="Write a follow-up email to Sarah thanking her for the interview and expressing enthusiasm about the role"
        )

        draft = draft_result["result"]["text"]

        # Step 2: Proofread
        print("\n✏️  Step 2: Proofread the draft")
        proofread_result = await self.demo.run_custom_scenario(
            action="proofread",
            text=draft
        )

        proofread = proofread_result["result"]["text"]

        # Step 3: Adjust tone if needed
        print("\n🎨 Step 3: Adjust tone to professional")
        final_result = await self.demo.run_custom_scenario(
            action="rewrite",
            text=proofread,
            params={"tone": "professional"}
        )

        print("\n✓ Final email ready to send!")

    async def meeting_notes_workflow(self):
        """Demo: Processing meeting notes"""

        print("\n" + "=" * 70)
        print("WORKFLOW DEMO: Meeting Notes Processing")
        print("=" * 70)

        notes = """
Meeting started 10am. Discussed Q4 roadmap. Sarah presented new features.
Team agreed on mobile app priority. John raised timeline concerns. Decided to hire contractor.
Action items: Sarah drafts spec, John interviews candidates. Next meeting Friday 2pm.
        """

        # Step 1: Extract key points
        print("\n📋 Step 1: Extract key points")
        key_points_result = await self.demo.run_custom_scenario(
            action="key_points",
            text=notes
        )

        # Step 2: Convert to numbered list
        print("\n🔢 Step 2: Convert action items to numbered list")
        action_items = "Sarah drafts spec. John interviews candidates."
        list_result = await self.demo.run_custom_scenario(
            action="make_numbered_list",
            text=action_items
        )

        # Step 3: Create summary
        print("\n📝 Step 3: Create executive summary")
        summary_result = await self.demo.run_custom_scenario(
            action="summarize",
            text=notes
        )

        print("\n✓ Meeting notes processed and ready to share!")

    async def document_editing_workflow(self):
        """Demo: Document editing workflow"""

        print("\n" + "=" * 70)
        print("WORKFLOW DEMO: Document Editing")
        print("=" * 70)

        doc = """
In my personal opinion, I think that the new feature will probably improve the user experience
by making things faster and easier to use. It might require some backend changes and frontend
updates. We should maybe consider implementing it soon.
        """

        # Step 1: Make more concise
        print("\n✂️  Step 1: Make more concise")
        concise_result = await self.demo.run_custom_scenario(
            action="rewrite",
            text=doc,
            params={"style": "concise"}
        )

        concise = concise_result["result"]["text"]

        # Step 2: Make professional
        print("\n💼 Step 2: Adjust to professional tone")
        professional_result = await self.demo.run_custom_scenario(
            action="rewrite",
            text=concise,
            params={"tone": "professional"}
        )

        # Step 3: Proofread final version
        print("\n✏️  Step 3: Final proofread")
        final_result = await self.demo.run_custom_scenario(
            action="proofread",
            text=professional_result["result"]["text"]
        )

        print("\n✓ Document polished and ready!")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main demo entry point"""

    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        demo = InlineAIDemo(mock_mode=True)

        if command == "all":
            # Run all scenarios
            await demo.run_all_scenarios()

        elif command == "interactive":
            # Interactive mode
            await demo.run_interactive_demo()

        elif command == "workflows":
            # Run workflow demos
            workflow_demo = WorkflowDemo()
            await workflow_demo.email_writing_workflow()
            await workflow_demo.meeting_notes_workflow()
            await workflow_demo.document_editing_workflow()

        elif command.startswith("scenario:"):
            # Run specific scenario by name
            scenario_name = command.split(":", 1)[1]
            scenario = next((s for s in DEMO_SCENARIOS if s.name.lower() == scenario_name.lower()), None)

            if scenario:
                await demo.run_scenario(scenario)
            else:
                print(f"Scenario '{scenario_name}' not found")
                print("\nAvailable scenarios:")
                for s in DEMO_SCENARIOS:
                    print(f"  - {s.name}")

        else:
            print(f"Unknown command: {command}")
            print_usage()

    else:
        # Default: run all scenarios
        demo = InlineAIDemo(mock_mode=True)
        await demo.run_all_scenarios()


def print_usage():
    """Print usage information"""

    print("""
Usage: python inline_ai_demo.py [command]

Commands:
  all             Run all demo scenarios (default)
  interactive     Interactive demo mode
  workflows       Run workflow demos
  scenario:<name> Run specific scenario by name

Examples:
  python inline_ai_demo.py
  python inline_ai_demo.py all
  python inline_ai_demo.py interactive
  python inline_ai_demo.py workflows
  python inline_ai_demo.py scenario:"Proofread Email"

Available scenarios:
""")

    for scenario in DEMO_SCENARIOS:
        print(f"  - {scenario.name}")


if __name__ == "__main__":
    asyncio.run(main())
