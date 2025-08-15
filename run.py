if __name__ == "__main__":
    from app.discord_bot import main
    import asyncio

    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("봇이 종료되었습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")
            raise