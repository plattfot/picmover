#include <catch.hpp>
#include <picmover/picmover.hpp>
#include <iostream>
#include <fstream>

TEST_CASE("IO")
{
  const picmover::fs::path sandbox = PICMOVER_STRINGIFY( PICMOVER_TEST_PATH )"/sandbox";
  REQUIRE( !sandbox.empty() );

  // Setup sandbox
  if( picmover::fs::exists(sandbox) )
    picmover::fs::remove_all( sandbox );

  picmover::fs::create_directories( sandbox );
  std::ofstream(sandbox/"image.nef" );
  std::ofstream(sandbox/"image.raw");
  std::ofstream(sandbox/"file");
  std::ofstream(sandbox/"image0.jpeg");
  std::ofstream(sandbox/"image1.jpeg");
  std::ofstream(sandbox/"readme.txt");
  picmover::fs::create_directory(sandbox/"subdir");
  std::ofstream(sandbox/"subdir/image3.jpeg");
  std::ofstream(sandbox/"subdir/image3.nef");
  std::ofstream(sandbox/"subdir/readme.txt");

  picmover::Files expected = {"file",
                              "image.nef",
                              "image.raw",
                              "image0.jpeg",
                              "image1.jpeg",
                              "readme.txt"};

  auto files = picmover::read( sandbox );

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

  CHECK( picmover::fs::remove_all( sandbox ) > 0 );
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

  SECTION("Filter out nef using lambda")
  {
    auto nef_files =
      std::move( picmover::filter
                 ( files, [regex = std::regex("\\.nef")]( const picmover::fs::path& file )
      {
        return std::regex_search( file.string(), regex );
      }));
    
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

TEST_CASE("Attributes")
{
  const picmover::fs::path images = PICMOVER_STRINGIFY( PICMOVER_TEST_PATH )"/images";

  SECTION("Maker")
  {
    picmover::Corrections corrections;
    corrections.emplace_back( [regex = std::regex("nikon", std::regex::icase)]
                              ( const std::string& str)
                              {
                                using Optional = std::optional<std::string>;
                                return std::regex_search(str, regex)? Optional("Nikon")
                                  : Optional();
                              });
    
    picmover::MakerAttribute make( corrections );
    
    auto maker = make( images/"DSC_3863.NEF" ); // Nikon D750
    
    CHECK( maker == "Nikon" );
  }

  SECTION("Model")
  {
    picmover::Corrections corrections;
    corrections.emplace_back( [regex = std::regex("nikon (D[0-9]+)", std::regex::icase)]
                              ( const std::string& str)
                              {
                                using Optional = std::optional<std::string>;
                                std::smatch model;

                                return std::regex_search(str, model, regex)
                                  ? Optional(model[1])
                                  : Optional();
                              });
    
    picmover::ModelAttribute model( corrections );
    
    auto camera_model = model( images/"DSC_3863.NEF" ); // Nikon D750
    
    CHECK( camera_model == "D750" );
  }
}
