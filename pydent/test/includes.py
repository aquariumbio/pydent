import aq

aq.login()

st = aq.SampleType.find_by_name("Enzyme")

# If you include the sample type, then Trident knows to convert the resulting
# data into a SampleTypeRecord

samples = aq.Sample.where(
  { "sample_type_id": st.id },
  { "include": "sample_type" },
  { "limit": 3 }
)

print(samples[0].sample_type)

# If you don't include the sample type, then Trident will fetch the
# sample type in a separate query. The interface looks the same, but
# this second version is slower.

samples = aq.Sample.where(
  { "sample_type_id": st.id },
  { },
  { "limit": 3 }
)

print(samples[0].sample_type)
