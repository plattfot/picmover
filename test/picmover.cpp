#include <catch.hpp>
#include <picmover/picmover.hpp>
#include <iostream>

TEST_CASE("IO")
{
  picmover::fs::path sandbox = PICMOVER_STRINGIFY( PICMOVER_SANDBOX_PATH );
  auto files = picmover::read( sandbox );

  picmover::Files expected = {"file",
                              "image.nef",
                              "image.raw",
                              "image0.jpeg",
                              "image1.jpeg",
                              "readme.txt"};
  SECTION("Reading files in")
  {
    for( const auto& expect : expected )
      {
        REQUIRE( std::find_if( files.begin(), files.end(),
                               [&]( const picmover::fs::path& path )
                               {
                                 return expect == path.filename();
                               }) != files.end() );
      }
  }

  SECTION("Copy files")
  {
    picmover::copy(files, sandbox/"dest");

    auto dest_files = picmover::read( sandbox/"dest" );
    
    REQUIRE( std::equal( files.begin(), files.end(), dest_files.begin(),
                         []( const picmover::fs::path& a, 
                             const picmover::fs::path& b)
                         {
                           return a.filename() == b.filename();
                         }));
  }
}

TEST_CASE("Filter and grouping")
{
  picmover::Files files = {"build/sandbox/image.nef",
                           "build/sandbox/image.raw",
                           "build/sandbox/file",
                           "build/sandbox/image0.jpeg",
                           "build/sandbox/image1.jpeg",
                           "build/sandbox/readme.txt"};

  SECTION("Filter out nothing")
  {
    auto all_files = std::move( picmover::filter( files, []( const picmover::fs::path& )
      {
        return true;
      } ));
    
    REQUIRE( all_files.size() == 6 );
  }
  
  SECTION("Filter out everything")
  {
    auto all_files = std::move( picmover::filter( files, []( const picmover::fs::path& )
      {
        return false;
      } ));
    
    REQUIRE( all_files.empty() );
  }

  SECTION("Filter out nef")
  {
    auto nef_files =
      std::move( picmover::filter( files, picmover::RegexFilter(std::regex("\\.nef")) ));
    
    REQUIRE( nef_files.size() == 1 );
  }

  SECTION("Filter out files with no extension")
  {
    auto ext_files =
      std::move( picmover::filter( files, picmover::RegexFilter(std::regex("\\..*")) ));
    
    REQUIRE( ext_files.size() == 5 );
  }

  SECTION("Group by extensions")
  {
    auto exts = 
      std::move( picmover::groupBy( files, []( const picmover::fs::path& file )
      {
        return file.has_extension() ? file.extension().string() : "unknown";
      }));
    
    CHECK( exts.size() == 5 );

    CHECK( exts[".jpeg"].size() == 2 );
    CHECK( exts[".nef"].size() == 1 );
    CHECK( exts[".txt"].size() == 1 );
    CHECK( exts[".raw"].size() == 1 );
    CHECK( exts["unknown"].size() == 1 );
    CHECK( exts["bob"].size() == 0 );
  }
}

