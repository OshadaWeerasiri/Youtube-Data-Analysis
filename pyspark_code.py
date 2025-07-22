import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.transforms import ApplyMapping, ResolveChoice, DropNullFields
from awsglue.utils import getResolvedOptions
from awsglue.job import Job

# Get job arguments
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Create context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Create and initialize job
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Predicate to filter regions
predicate_pushdown = "region in ('ca','gb','us')"

# Read from AWS Glue Data Catalog
datasource0 = glueContext.create_dynamic_frame.from_catalog(
    database="de-youtube-raw",
    table_name="raw_statistics",
    push_down_predicate=predicate_pushdown,
    transformation_ctx="datasource0"
)

# Apply mapping
applymapping1 = ApplyMapping.apply(
    frame=datasource0,
    mappings=[
        ("video_id", "string", "video_id", "string"),
        ("trending_date", "string", "trending_date", "string"),
        ("title", "string", "title", "string"),
        ("channel_title", "string", "channel_title", "string"),
        ("category_id", "long", "category_id", "long"),
        ("publish_time", "string", "publish_time", "string"),
        ("tags", "string", "tags", "string"),
        ("views", "long", "views", "long"),
        ("likes", "long", "likes", "long"),
        ("dislikes", "long", "dislikes", "long"),
        ("comment_count", "long", "comment_count", "long"),
        ("thumbnail_link", "string", "thumbnail_link", "string"),
        ("comments_disabled", "boolean", "comments_disabled", "boolean"),
        ("ratings_disabled", "boolean", "ratings_disabled", "boolean"),
        ("video_error_or_removed", "boolean", "video_error_or_removed", "boolean"),
        ("description", "string", "description", "string"),
        ("region", "string", "region", "string")
    ],
    transformation_ctx="applymapping1"
)

# Resolve choice (if needed)
resolvechoice2 = ResolveChoice.apply(
    frame=applymapping1,
    choice="make_cols",
    transformation_ctx="resolvechoice2"
)

# Drop null fields
dropnullfields3 = DropNullFields.apply(
    frame=resolvechoice2,
    transformation_ctx="dropnullfields3"
)

# Convert to DataFrame and coalesce to 1 file per region
df = dropnullfields3.toDF().coalesce(1)

# Convert back to DynamicFrame
final_dynamic_frame = DynamicFrame.fromDF(df, glueContext, "final_dynamic_frame")

# Write to S3 in parquet format with partitioning by region
datasink4 = glueContext.write_dynamic_frame.from_options(
    frame=final_dynamic_frame,
    connection_type="s3",
    connection_options={
        "path": "s3://youtubedataen-cleaned/youtube/raw_statistics/",
        "partitionKeys": ["region"]
    },
    format="parquet",
    transformation_ctx="datasink4"
)

# Commit the job
job.commit()
