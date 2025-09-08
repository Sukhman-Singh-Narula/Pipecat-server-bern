"""
Conversation Service for managing conversation transcripts and summaries
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from server.models.conversation import ConversationTranscript, ConversationSummary, ConversationMessage
from server.services.firebase_service import FirebaseService

class ConversationService:
    """Service for managing conversation transcripts and summaries"""
    
    def __init__(self, firebase_service: FirebaseService):
        self.firebase = firebase_service
        self.transcripts_collection = "conversation_transcripts"
        self.summaries_collection = "conversation_summaries"
    
    async def create_conversation(self, user_email: str, season: int, episode: int) -> str:
        """Create a new conversation session"""
        try:
            conversation_id = f"{user_email}_{season}_{episode}_{int(datetime.utcnow().timestamp())}"
            
            transcript = ConversationTranscript(
                conversation_id=conversation_id,
                user_email=user_email,
                season=season,
                episode=episode
            )
            
            await self.firebase.set_document(
                self.transcripts_collection,
                conversation_id,
                transcript.to_dict()
            )
            
            logger.info(f"Created conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def add_message(self, conversation_id: str, speaker: str, content: str, message_type: str = "text") -> bool:
        """Add a message to the conversation"""
        try:
            transcript = await self.get_conversation_transcript(conversation_id)
            if not transcript:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            
            message = ConversationMessage(
                speaker=speaker,
                content=content,
                message_type=message_type
            )
            
            transcript.add_message(message)
            
            await self.firebase.update_document(
                self.transcripts_collection,
                conversation_id,
                transcript.to_dict()
            )
            
            logger.info(f"Added message to conversation {conversation_id}: {speaker}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            return False
    
    async def get_conversation_transcript(self, conversation_id: str) -> Optional[ConversationTranscript]:
        """Get conversation transcript by ID"""
        try:
            data = await self.firebase.get_document(self.transcripts_collection, conversation_id)
            if data:
                return ConversationTranscript.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation transcript {conversation_id}: {e}")
            return None
    
    async def get_user_conversations(self, user_email: str, limit: Optional[int] = None) -> List[ConversationTranscript]:
        """Get all conversations for a user"""
        try:
            conversations_data = await self.firebase.query_collection(
                self.transcripts_collection,
                [("user_email", "==", user_email)]
            )
            
            conversations = [ConversationTranscript.from_dict(data) for data in conversations_data]
            # Sort by start time descending (most recent first)
            conversations.sort(key=lambda x: x.start_time, reverse=True)
            
            if limit:
                conversations = conversations[:limit]
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting user conversations for {user_email}: {e}")
            return []
    
    async def get_episode_conversations(self, season: int, episode: int) -> List[ConversationTranscript]:
        """Get all conversations for a specific episode"""
        try:
            conversations_data = await self.firebase.query_collection(
                self.transcripts_collection,
                [("season", "==", season), ("episode", "==", episode)]
            )
            
            conversations = [ConversationTranscript.from_dict(data) for data in conversations_data]
            # Sort by start time descending
            conversations.sort(key=lambda x: x.start_time, reverse=True)
            
            return conversations
        except Exception as e:
            logger.error(f"Error getting episode conversations S{season}E{episode}: {e}")
            return []
    
    async def finish_conversation(self, conversation_id: str, completion_status: str = "completed") -> bool:
        """Mark conversation as finished and calculate duration"""
        try:
            transcript = await self.get_conversation_transcript(conversation_id)
            if not transcript:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            
            transcript.finish_conversation(completion_status)
            
            await self.firebase.update_document(
                self.transcripts_collection,
                conversation_id,
                transcript.to_dict()
            )
            
            logger.info(f"Finished conversation {conversation_id}: {completion_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error finishing conversation {conversation_id}: {e}")
            return False
    
    async def create_conversation_summary(self, conversation_id: str, summary_data: Dict[str, Any]) -> ConversationSummary:
        """Create a summary for a completed conversation"""
        try:
            transcript = await self.get_conversation_transcript(conversation_id)
            if not transcript:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            summary = ConversationSummary(
                conversation_id=conversation_id,
                user_email=transcript.user_email,
                season=transcript.season,
                episode=transcript.episode,
                session_summary=summary_data.get("session_summary", ""),
                key_learnings=summary_data.get("key_learnings", []),
                words_learned=summary_data.get("words_learned", []),
                topics_covered=summary_data.get("topics_covered", []),
                performance_rating=summary_data.get("performance_rating", 5),
                engagement_level=summary_data.get("engagement_level", "high"),
                areas_for_improvement=summary_data.get("areas_for_improvement", []),
                next_recommendations=summary_data.get("next_recommendations", [])
            )
            
            await self.firebase.set_document(
                self.summaries_collection,
                conversation_id,
                summary.to_dict()
            )
            
            logger.info(f"Created conversation summary: {conversation_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
            raise
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[ConversationSummary]:
        """Get conversation summary by conversation ID"""
        try:
            data = await self.firebase.get_document(self.summaries_collection, conversation_id)
            if data:
                return ConversationSummary.from_dict(data)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation summary {conversation_id}: {e}")
            return None
    
    async def get_user_summaries(self, user_email: str, limit: Optional[int] = None) -> List[ConversationSummary]:
        """Get all conversation summaries for a user"""
        try:
            summaries_data = await self.firebase.query_collection(
                self.summaries_collection,
                [("user_email", "==", user_email)]
            )
            
            summaries = [ConversationSummary.from_dict(data) for data in summaries_data]
            # Sort by created date descending
            summaries.sort(key=lambda x: x.created_at, reverse=True)
            
            if limit:
                summaries = summaries[:limit]
            
            return summaries
        except Exception as e:
            logger.error(f"Error getting user summaries for {user_email}: {e}")
            return []
    
    async def get_conversation_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a conversation"""
        try:
            transcript = await self.get_conversation_transcript(conversation_id)
            summary = await self.get_conversation_summary(conversation_id)
            
            if not transcript:
                return {}
            
            analytics = {
                "conversation_info": {
                    "conversation_id": conversation_id,
                    "user_email": transcript.user_email,
                    "season": transcript.season,
                    "episode": transcript.episode,
                    "status": transcript.status
                },
                "timing": {
                    "start_time": transcript.start_time,
                    "end_time": transcript.end_time,
                    "duration_seconds": transcript.duration_seconds,
                    "duration_minutes": round(transcript.duration_seconds / 60, 2) if transcript.duration_seconds else 0
                },
                "message_stats": {
                    "total_messages": len(transcript.messages),
                    "user_messages": len([m for m in transcript.messages if m.speaker == "user"]),
                    "bot_messages": len([m for m in transcript.messages if m.speaker == "bot"]),
                    "system_messages": len([m for m in transcript.messages if m.speaker == "system"])
                }
            }
            
            if summary:
                analytics["learning_summary"] = {
                    "performance_rating": summary.performance_rating,
                    "engagement_level": summary.engagement_level,
                    "words_learned": summary.words_learned,
                    "topics_covered": summary.topics_covered,
                    "key_learnings": summary.key_learnings,
                    "areas_for_improvement": summary.areas_for_improvement,
                    "next_recommendations": summary.next_recommendations
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting conversation analytics for {conversation_id}: {e}")
            return {}
    
    async def get_user_learning_progression(self, user_email: str) -> Dict[str, Any]:
        """Get user's learning progression across all conversations"""
        try:
            summaries = await self.get_user_summaries(user_email)
            transcripts = await self.get_user_conversations(user_email)
            
            if not summaries and not transcripts:
                return {}
            
            # Aggregate learning data
            all_words_learned = []
            all_topics_covered = []
            total_session_time = 0
            session_count = 0
            ratings = []
            
            for summary in summaries:
                all_words_learned.extend(summary.words_learned)
                all_topics_covered.extend(summary.topics_covered)
                ratings.append(summary.performance_rating)
            
            for transcript in transcripts:
                if transcript.duration_seconds:
                    total_session_time += transcript.duration_seconds
                    session_count += 1
            
            # Calculate progression metrics
            unique_words = list(set(all_words_learned))
            unique_topics = list(set(all_topics_covered))
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            avg_session_time = total_session_time / session_count if session_count > 0 else 0
            
            return {
                "user_email": user_email,
                "learning_stats": {
                    "total_sessions": len(transcripts),
                    "completed_sessions": len(summaries),
                    "total_words_learned": len(unique_words),
                    "total_topics_covered": len(unique_topics),
                    "unique_words": unique_words,
                    "unique_topics": unique_topics
                },
                "performance": {
                    "average_rating": round(avg_rating, 2),
                    "total_learning_time_seconds": total_session_time,
                    "total_learning_time_hours": round(total_session_time / 3600, 2),
                    "average_session_time_minutes": round(avg_session_time / 60, 2)
                },
                "recent_activity": {
                    "last_session": transcripts[0].start_time if transcripts else None,
                    "recent_conversations": [t.conversation_id for t in transcripts[:5]]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user learning progression for {user_email}: {e}")
            return {}
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its summary"""
        try:
            # Delete transcript
            await self.firebase.delete_document(self.transcripts_collection, conversation_id)
            
            # Delete summary if exists
            summary = await self.get_conversation_summary(conversation_id)
            if summary:
                await self.firebase.delete_document(self.summaries_collection, conversation_id)
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    async def search_conversations(self, user_email: str, search_term: str) -> List[ConversationTranscript]:
        """Search user's conversations by content"""
        try:
            conversations = await self.get_user_conversations(user_email)
            search_term_lower = search_term.lower()
            
            matching_conversations = []
            for conversation in conversations:
                # Search in messages
                for message in conversation.messages:
                    if search_term_lower in message.content.lower():
                        matching_conversations.append(conversation)
                        break
            
            return matching_conversations
        except Exception as e:
            logger.error(f"Error searching conversations for {user_email} with term '{search_term}': {e}")
            return []
