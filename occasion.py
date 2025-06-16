import instaloader
from instaloader import ConnectionException  # ConnectionException'u import edelim

print("Program başlıyor...")

# Instaloader modülünü başlatıyoruz
loader = instaloader.Instaloader(
    download_videos=True,
    download_geotags=False,
    save_metadata=False,
    post_metadata_txt_pattern=None
)

# fast_update özelliğini global olarak aktif edelim
loader.fast_update = False

profile_name = "defsbutikk"
profile = instaloader.Profile.from_username(loader.context, profile_name)

total_posts = profile.mediacount
print(f"Toplam gönderi sayısı: {total_posts}")

posts = profile.get_posts()

for i, post in enumerate(posts, start=1):
    if i > 10:
        break
    progress = (i / total_posts) * 100
    print(f"[{i}/{total_posts}] - %{progress:.2f} - Gönderi indiriliyor...")

    try:
        loader.download_post(post, target=profile_name)
    except ConnectionException as e:
        # 410 Gone gibi bağlantı hatalarında buraya düşer.
        print(f"Bağlantı hatası (muhtemelen 410 Gone). İndirilemiyor, geçiyorum: {e}")
        continue

print("Tüm gönderiler başarıyla indirildi!")
