from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("VoiceDemo").getOrCreate()

df = spark.read.text("../data/transcripts.json")

df.show()

spark.stop()