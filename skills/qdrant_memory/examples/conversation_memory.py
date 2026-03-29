#!/usr/bin/env python3
"""
Conversation memory example for Qdrant Memory Skill
Demonstrates storing and retrieving conversation history
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import (
    save_text, load_text, get_all_texts, list_collections,
    create_collection, delete_collection, test_connection
)


class ConversationMemory:
    """Simple conversation memory using Qdrant"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.collection_name = f"conversations_{user_id}"
        
    def initialize(self):
        """Initialize conversation storage"""
        if not test_connection():
            print("Qdrant connection failed")
            return False
        
        # Collection will be auto-created on first save
        return True
    
    def add_message(self, role: str, content: str, additional_metadata: dict = None):
        """
        Add a message to conversation history
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            additional_metadata: Additional metadata
        """
        metadata = {
            "user_id": self.user_id,
            "role": role,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        doc_id = save_text(self.collection_name, content, metadata)
        return doc_id
    
    def get_recent_messages(self, limit: int = 10):
        """Get recent messages from conversation"""
        messages = get_all_texts(self.collection_name, limit=limit)
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x.get('metadata', {}).get('timestamp', ''), reverse=True)
        
        return messages
    
    def get_conversation_context(self, limit: int = 5):
        """Get conversation context for LLM prompts"""
        messages = self.get_recent_messages(limit=limit)
        
        context = []
        for msg in messages:
            role = msg['metadata'].get('role', 'unknown')
            content = msg['text']
            context.append(f"{role}: {content}")
        
        return "\n".join(context)
    
    def clear_conversation(self):
        """Clear conversation history"""
        return delete_collection(self.collection_name)


def main():
    """Demonstrate conversation memory usage"""
    print("=== Qdrant Memory Skill - Conversation Memory Example ===\n")
    
    # Create conversation memory for a user
    user_id = "bob"
    memory = ConversationMemory(user_id)
    
    print(f"1. Initializing conversation memory for user '{user_id}'...")
    if memory.initialize():
        print("   ✓ Conversation memory initialized")
    else:
        print("   ✗ Initialization failed")
        return 1
    
    # Simulate a conversation
    print("\n2. Simulating conversation...")
    
    conversation = [
        ("user", "Hallo Eva, wie geht es dir heute?"),
        ("assistant", "Hallo Bob! Mir geht es gut, danke der Nachfrage. Wie kann ich dir helfen?"),
        ("user", "Kannst du mir bei ROS 2 helfen?"),
        ("assistant", "Ja, natürlich! ROS 2 ist ein Robot Operating System. Was genau möchtest du wissen?"),
        ("user", "Wie starte ich einen ROS 2 Node?"),
        ("assistant", "Du kannst einen ROS 2 Node mit 'ros2 run <package> <node>' starten. Möchtest du ein konkretes Beispiel?"),
        ("user", "Ja, zeig mir ein Beispiel mit turtlesim."),
        ("assistant", "Sicher! Öffne ein Terminal und führe aus: 'ros2 run turtlesim turtlesim_node'. Dann öffne ein zweites Terminal für: 'ros2 run turtlesim turtle_teleop_key'.")
    ]
    
    for role, content in conversation:
        doc_id = memory.add_message(role, content)
        if doc_id:
            print(f"   ✓ {role}: {content[:40]}...")
        else:
            print(f"   ✗ Failed to save message")
    
    # Retrieve conversation context
    print("\n3. Retrieving conversation context...")
    context = memory.get_conversation_context(limit=4)
    print("   Recent conversation:")
    print("   " + "-" * 50)
    for line in context.split('\n'):
        print(f"   {line}")
    print("   " + "-" * 50)
    
    # Show all messages
    print("\n4. Showing all stored messages...")
    all_messages = memory.get_recent_messages(limit=20)
    print(f"   Total messages stored: {len(all_messages)}")
    
    for i, msg in enumerate(all_messages, 1):
        role = msg['metadata'].get('role', 'unknown')
        timestamp = msg['metadata'].get('timestamp', '')
        content_preview = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
        
        print(f"\n   {i}. {role.upper()} ({timestamp}):")
        print(f"      {content_preview}")
    
    # Demonstrate how this could be used with an LLM
    print("\n5. Example LLM context preparation...")
    llm_context = memory.get_conversation_context(limit=3)
    
    print("   Context for LLM prompt:")
    print('   """')
    print(f"   Conversation history:\n{llm_context}")
    print('   """')
    print("\n   This context can be prepended to LLM prompts for continuity.")
    
    # Clean up
    print("\n6. Cleaning up...")
    print("   Deleting conversation history...")
    if memory.clear_conversation():
        print("   ✓ Conversation history deleted")
    else:
        print("   ✗ Failed to delete history")
    
    print("\n=== Conversation Memory Example Completed ===")
    print("\nPotential enhancements:")
    print("1. Add message threading/conversation IDs")
    print("2. Implement message search by content")
    print("3. Add message expiration/archiving")
    print("4. Integrate with actual LLM for response generation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())