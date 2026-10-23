
Sourcing music for AI training requires strict attention to copyright, as major music labels actively pursue legal action against models trained on unlicensed content.
When looking for public domain music, you must account for the "two-pronged" nature of music copyright: the musical composition (the written notes and lyrics) and the sound recording (the specific audio file). While a classical piece written by Beethoven is in the public domain, a recording of a modern orchestra playing it is protected by copyright.
The best platforms and structured datasets that explicitly provide public domain sound recordings and metadata for research and AI training include:

1. The Free Music Archive (FMA) Dataset

• What it is: A heavily utilized open dataset specifically structured for music analysis and machine learning. The full dataset contains over 100,000 high-definition, full-length tracks with pre-computed features and clean metadata.
• How to use it for AI: While the entire archive contains mixed licenses, you can filter or target the specific subset dedicated to the public domain. The Citizen DJ FMA Subset hosts an isolated collection of FMA recordings that creators have officially placed under a Creative Commons Public Domain Dedication (CC0) license.

2. The Library of Congress (Citizen DJ Project)

• What it is: Under the U.S. Music Modernization Act, historical sound recordings published in 1925 or earlier are officially in the public domain.
• How to use it for AI: The Library of Congress launched the Citizen DJ Platform, which provides thousands of free, downloadable audio samples specifically curated for machine learning, remixing, and data analysis. This dataset includes thousands of early 20th-century recordings spanning classical, opera, early jazz, and blues.

3. The Internet Archive (Great 78 Project)

• What it is: A massive repository holding hundreds of thousands of digitized, historical sound recordings.
• How to use it for AI: You can programmatically filter the Internet Archive Audio Library for items marked as "Public Domain" or "CC0". Specifically, the Great 78 Project hosts over 400,000 digitized 78-rpm records from the early 20th century. Because these acoustic recordings were published before the mid-1920s, their physical audio tracks are completely public domain under U.S. law.

4. Open-Source AI Repositories (MusOpen)

• What it is: A non-profit site focused on freeing music by providing sheet music, education materials, and audio recordings completely free of copyright restrictions.
• How to use it for AI: You can browse the MusOpen Royalty-Free Music Archive and specifically filter by the "Public Domain" license. They crowdsource and fund new, professional recordings of classical compositions (like Bach, Mozart, and Beethoven) and release the resulting audio files directly into the public domain so they are safe to scrape for training text-to-music or generation models.

Alternative Option: Synthetic Audio Datasets

If your AI model requires clean, modern, multi-track audio rather than historical recordings, look into synthetic music datasets. AI-generated audio tracks that lack human authorship cannot be copyrighted under current U.S. Copyright Office rules. Developers frequently use open-weights tools like ACE-Step to generate massive amounts of uncopyrighted, synthetic music files specifically to expand their downstream machine learning training sets.
What specific type of model are you trying to train (e.g., symbolic music generation like MIDI, text-to-audio generation, or audio source separation)? I can recommend datasets tailored to that format.

Starting from scratch gives you a blank slate to design your architecture perfectly, but it means managing the raw audio pipeline and metadata alignment is entirely up to you.
When building a custom model from the ground up, your primary bottleneck isn't just finding public domain files—it's how those files are formatted, labeled, and prepared for your neural network.
The best datasets for the early development stages of a custom music AI model are grouped below by the specific training style they support:

1. For Audio-to-Audio / Generative Models (Raw Waveforms)

If you are building a model like a custom diffusion network, a VAE, or a neural audio codec that needs raw audio files, you need large chunks of continuous sound.
• The FMA Full Dataset: This is the gold standard for custom audio development. You can download it directly from GitHub or academic mirrors. It contains 917 GiB of uncompressed audio spanning 106,574 tracks. While the whole dataset is mixed, it includes a comprehensive metadata spreadsheet (tracks.csv) containing strict license columns, allowing you to instantly isolate and ingest only the tracks explicitly labeled as Creative Commons Attribution or Public Domain / CC0.
• The Great 78 Project Bulk Downloads: The Internet Archive allows you to use wget or their command-line tool to programmatically download historical audio files in bulk. Because these are early acoustic recordings, they are excellent for training a model to understand fundamental musical structures (melody, rhythm, instrument separation) without getting bogged down by hyper-polished modern production tricks.

2. For Text-to-Audio / Description Models (Prompting)

If your custom model needs to translate text descriptions into music, you must have aligned text captions alongside the audio data.
• MusicCaps (via Hugging Face): While the underlying audio comes from YouTube, the dataset itself is an open-source, public-domain evaluation set created by Google researchers. It contains 5,521 music clips paired with professional, highly detailed, text-based descriptions written by musicians (covering genre, mood, instrumentation, and tempo). It is an excellent dataset to use for building the text-embedding layer of a custom prompt-based model.

3. For Symbolic Models (MIDI / Composition)

If you are building a transformer model (similar to how LLMs handle text) to predict notes, chords, and timing rather than synthesizing raw sound waves, you need symbolic data.
• The Lakh MIDI Dataset (LMD): A massive collection of 178,284 unique MIDI files, many of which are matched to clean audio recordings. Because MIDI data contains exact pitch numbers, velocity, and timestamp markers, it uses a fraction of the computational power and token costs required for raw audio processing. It is perfect for training a custom model to understand music theory and composition logic before you even touch raw sound synthesis.

Key Technical Advice for Early Development

• Standardize Your Sample Rate: Public domain audio comes from hundreds of different sources at different sample rates (e.g., historical tracks at 22,050 Hz, modern tracks at 44,100 Hz or 48,000 Hz). Create a preprocessing script using a tool like Python's librosa or FFmpeg to downsample or upsample every single training file to a uniform rate before feeding it to your model.
• Beware of Historical Noise: If you use early 20th-century recordings from the Library of Congress or the Great 78 Project, the files will contain heavy surface noise, clicks, and pops from the original vinyl or wax cylinders. Your model will learn this noise as part of what "music" is. If you want a clean sound, you will need to pass the audio through a de-noising pre-processing layer first.
Are you leaning toward processing symbolic data (like MIDI or sheet music) or working directly with raw audio signals (like WAV or MP3 files)? I can provide code snippets or ingestion workflows for whichever direction you choose.

Strictly speaking, truly "modern" commercial music (like recent pop, rock, or hip-hop) cannot be in the public domain, because U.S. and international copyright laws protect compositions and recordings for decades (compositions published in the U.S. in 1930 or earlier are currently in the public domain as of 2026, while 1931 enters next year).
However, you can find contemporary-sounding or newly created music that is free to use without paying royalties by looking at alternative licensing or open-access channels:

Where to Find Modern-Style Free & Open Music

• Free Music Archive (FMA): A massive library featuring modern genres (hip-hop, electronic, indie, pop) shared under Creative Commons (CC) licenses or public domain designations. Check individual track permissions, as some require attribution or non-commercial use.
• ccMixter: A community-driven platform where musicians upload modern, beat-driven, and instrumental tracks specifically meant for remixing and free use under Creative Commons terms.
• Internet Archive: Use the Advanced Search tool to filter audio collections by media type and year, giving you access to user-uploaded live concerts, netlabels, and open-source contemporary recordings.
• Musopen: Offers free sheet music and royalty-free/public domain recordings, including modern recordings and new performances of classical or neoclassical pieces.
• Library of Congress - Citizen DJ: Lets you browse and remix historical audio and public domain sound recordings, which can be chopped up or re-produced into modern beats.

Important Distinction to Keep in Mind

• Composition vs. Recording: Even if a song's underlying composition is old enough to be public domain (e.g., a traditional folk song or a 1920s jazz standard), a modern recording of that song is still copyrighted by the artist or label who performed it. To stay completely legal, use a version recorded over 100 years ago, record your own cover, or use music explicitly released under Creative Commons or public domain waivers.
Are you planning to use this music for a commercial project (like a YouTube video, podcast, or game), or are you looking for sheet music to play/perform? Let me know so I can point you to the right license type.

For training a custom machine learning model, downloading tracks one by one from retail or consumer-facing websites is wildly inefficient. You need pre-curated, structured datasets where the licensing is strictly CC0 (Creative Commons Zero / Public Domain) to ensure clean, ethical AI training data without copyright liability.
The most viable open-source, CC0, and freely licensed datasets for building a small AI music model include the following:

1. Structured CC0 Audio Datasets

If your model requires raw audio waveforms (WAV or MP3 formats), look into these curated repositories:
• SoundSafari CC0-1.0-Music Corpus: This is arguably the best starting point for audio training. It is a massive, pre-aggregated dataset containing ~7,000 public domain/CC0-1.0 licensed songs (~40GB of data) explicitly built for ethical audio machine learning and digital signal processing (DSP) experimentation. It pulls legal, modern-style audio from platforms like Chosic, Pixabay, and Free Music Archive, packaging them cleanly for developers.
• Free Music Archive (FMA Dataset): The full FMA corpus is available on Hugging Face as a massive dataset containing over 106,000 audio tracks (8,000+ hours of music) across 16 genres. Note: While it contains thousands of CC0/Public Domain tracks, it also includes restricted Creative Commons files (like Non-Commercial or Share-Alike). You will need to write a simple Python script to filter the metadata sheet by license == 'CC0' or license == 'Public Domain' before downloading the audio shards.
• MTG-Jamendo Dataset: A widely recognized open dataset for music information retrieval and generation. It includes over 55,000 full-length tracks across hundreds of tags. Like FMA, it uses mixed Creative Commons licenses, so you must programmatically filter for the CC0 subsets.

2. Symbolic Music Datasets (MIDI)

If you are building a symbolic generative model (like a transformer that generates note sequences, chords, or composition structures rather than raw audio waveforms):
• imslp-midi-cc0-1.0 on Hugging Face: A cleanly formatted dataset of over 1,100 unique MIDI files explicitly under the CC0 1.0 license. While it features classical and romantic eras, it also includes a designated "Modern" style category (148 tracks). The data can be loaded seamlessly via the Hugging Face datasets library as raw bytes, ready to be tokenized.
• Lakh MIDI Dataset: A massive collection of 174,533 unique MIDI files, many of which are matched to the Million Song Dataset. Because it contains a wide array of modern pop, rock, and electronic covers generated by users, it is standard for token-based generative music models. However, you must carefully vet the exact origin tracking if you require strict public-domain compliance.

3. Sourcing via Metadata & API Scrapers

If you want to build a custom pipeline to scrape metadata and download audio programmatically:
• MusicBrainz Database Dumps: MusicBrainz offers its comprehensive music metadata archives under CC0 data dumps. You can download their database to query tracking information, release years, and license mappings to pinpoint public domain compositions.
• Freesound.org API: Freesound hosts thousands of modern music loops, instrumental stems, and soundscapes. Their developer API allows you to programmatically filter search queries specifically for the license:"Creative Commons 0" tag, allowing you to scrape clean, modern loops directly into your local machine-learning environment.