from rest_framework import serializers
from .models import Chat, Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = ['sender', 'text', 'created_at']

class ChatSerializer(serializers.ModelSerializer):
    participant2 = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'participant2', 'messages']
    
    def get_participant2(self, obj):
        request = self.context.get('request')
        if obj.participant1 == request.user:
            return {
                'id': obj.participant2.id,
                'username': obj.participant2.username,
                'profile_image': obj.participant2.profile.image.url
            }
        else:
             return {
                'id': obj.participant1.id,
                'username': obj.participant1.username,
                'profile_image': obj.participant1.profile.image.url
            }

class ChatSerializerList(serializers.ModelSerializer):
    participant2 = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'participant2', 'messages']
    
    def get_participant2(self, obj):
        request = self.context.get('request')
        if obj.participant1 == request.user:
            return {
                'id': obj.participant2.id,
                'username': obj.participant2.username,
                'profile_image': obj.participant2.profile.image.url if obj.participant2.profile.image else None
            }
        else:
             return {
                'id': obj.participant1.id,
                'username': obj.participant1.username,
                'profile_image': obj.participant1.profile.image.url if obj.participant1.profile.image else None
            }