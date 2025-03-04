from django.db import models


class CategoryColours(models.TextChoices):
    GREEN = "#4CAF50", "Green"
    BLUE = "#00E5FF", "Blue"
    RED = "#D50000", "Red"
    ORANGE = "#FF6F00", "Orange"
    PURPLE = "#6200EA", "Purple"
    TURQUOISE = "#03DAC5", "Turquoise"
    PINK = "#FF0266", "Pink"
    YELLOW = "#FFD600", "Yellow"


class Category(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.CharField(max_length=60)
    colour = models.CharField(max_length=7, choices=CategoryColours, default=CategoryColours.BLUE)

    def __str__(self):
        return self.text
    
    class Meta:
        verbose_name_plural = "categories"

class Reason(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.CharField(max_length=60)
    machine_mapping = models.ManyToManyField("state.Machine", through='MachineReasonMap',
                                             related_name="reason_mapping")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    considered_downtime = models.BooleanField(default=True, help_text="Untick for reasons (like end of shift) that shouldn't be considered for Downtime")

    def __str__(self):
        return self.text

class MachineReasonMap(models.Model):
    id = models.BigAutoField(primary_key=True)
    reason = models.ForeignKey(Reason, on_delete=models.CASCADE)
    machine = models.ForeignKey("state.Machine", on_delete=models.CASCADE)
