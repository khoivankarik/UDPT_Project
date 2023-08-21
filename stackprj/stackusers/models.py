# stackusers/models.py
from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.utils import timezone
from stackbase.models import Comment, Question  # Import the models from the stackbase app

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=1000)
    phone = models.IntegerField(null=True, blank=True)
    image = models.ImageField(default='default.jpg', upload_to="profile_pic")
    score = models.PositiveIntegerField(default=0)  # New field for the score

    def __str__(self):
        return f'{self.user.username} - Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def update_score(self):
        questions_created = Question.objects.filter(user=self.user).count()
        comments_made = Comment.objects.filter(name=self.user.username).count()
        questions_liked = self.user.question_post.count()
        comments_liked = self.user.comment_likes.count()

        total_score = questions_created + comments_made + questions_liked + comments_liked
        self.score = total_score
        self.save()





